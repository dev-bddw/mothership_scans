import csv
import datetime
import io
import json
import random

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from requests.structures import CaseInsensitiveDict
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer

from .models import Fail, Scan, Success
from .serializers import ScanSerializer


@login_required
def scans_list(request):

    return render(
        request,
        "scans_list.html",
        {"scans": Scan.objects.all()},
    )


@login_required
def scans_sorting(request):

    sort_by = request.GET.get("sorting")

    return render(
        request,
        "scans_list.html",
        {"scans": Scan.objects.all().order_by(sort_by)},
    )


@login_required
def search_scans(request):
    if request.method == "POST":

        query = request.POST.get("search")
        scans = Scan.objects.filter(sku__startswith=query)

        if len(scans) == 0:

            scans = Scan.objects.filter(scan_id__startswith=query)

        return render(request, "partials/search.html", {"scans": scans})


def return_scans_by_sku(request, item_sku):

    order_by = (
        "-time_scan"
        if request.GET.get("sorting") is None
        else request.GET.get("sorting")
    )

    return render(
        request,
        "by_sku.html",
        {
            "scans": Scan.objects.filter(sku=item_sku).order_by(order_by),
            "sku": item_sku,
        },
    )


def return_scans_by_tn(request, tn):

    order_by = (
        "-time_scan"
        if request.GET.get("sorting") is None
        else request.GET.get("sorting")
    )

    return render(
        request,
        "by_tracking.html",
        {
            "scans": Scan.objects.filter(tracking=tn).order_by(order_by),
            "tn": tn,
        },
    )


def return_scans_by_location(request, location):

    order_by = (
        "-time_scan"
        if request.GET.get("sorting") is None
        else request.GET.get("sorting")
    )

    return render(
        request,
        "by_location.html",
        {
            "scans": Scan.objects.filter(location=location).order_by(order_by),
            "location": location,
        },
    )


@login_required
def send_all_scans(request):
    """
    send or resend all latest scans by tn that are marked bin_succcess False
    """

    bin_package = []

    for scan in Scan.objects.all().exclude(bin_succes=True):

        if scan.is_latest() and scan.has_tracking():

            bin_package["data"].append(
                {
                    "type": "items",
                    "id": scan.tracking,
                    "attributes": {
                        "sku": scan.sku,
                        "location": scan.readable_location(),
                        "last_scan": str(scan.scan_id),
                    },
                }
            )

    # result = process_for_errors(create_and_send(bin_package))

    return JsonResponse()


@csrf_exempt
@api_view(["GET", "POST"])
def create_scan_api_endpoint_v2(request):

    batch_id = random.randint(0, 10000)

    for_processing = {
        "batch_id": batch_id,
        "data_from_terminal": request.data["data"],
        "terminal_response": {"data": []},
        "bin_request_body": {"data": []},
    }

    if request.method == "POST":

        # convert terminal data to scan records
        for scan in for_processing["data_from_terminal"]:
            try:
                print(scan["attributes"])
                defaults = scan["attributes"]
                defaults.update({"batch_id": batch_id, "scan_id": scan["id"]})
                Scan(**defaults).save()
            except ValueError:
                continue

        # prepare terminal response
        for scan in Scan.objects.filter(batch_id=batch_id):
            try:
                for_processing["terminal_response"]["data"].append(
                    {
                        "type": "scans",
                        "id": str(scan.scan_id),
                        "attributes": {
                            "time_upload": scan.time_upload.strftime(
                                "%Y-%m-%dT%H:%M:%S.%f%z"
                            ),
                        },
                    }
                )
            except ValueError:
                continue

        # prepare request body for bin api call
        for scan in Scan.objects.filter(batch_id=batch_id):
            try:
                for_processing["bin_request_body"]["data"].append(
                    {
                        "type": "items",
                        "id": scan.tracking,
                        "attributes": {
                            "sku": scan.sku,
                            "location": scan.readable_location(),
                            "last_scan": str(scan.scan_id),
                        },
                    }
                )

            except ValueError:
                continue

        # prepare to send patch request to update bin
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Content-type"] = "application/json"
        headers["Authorization"] = "Bearer {}".format(settings.BIN_KEY)

        # send request
        response = requests.patch(
            settings.BIN_API_ENDPOINT,
            data=json.dumps(for_processing["bin_request_body"]),
            headers=headers,
        )

        if response.status_code == 200:

            if response.json() == {"errors": []}:

                process_result = "BIN UPDATED WITH NO ERRORS"

                Scan.objects.filter(batch_id=batch_id).update(bin_success=True)

                [
                    Success.objects.create(scan=x, batch_id=batch_id)
                    for x in Scan.objects.filter(batch_id=batch_id)
                ]

            else:

                process_result = "BIN REACHED WITH ERRORS"

                r = response.json()

                Scan.objects.filter(batch_id=batch_id).update(bin_success=True)

                [
                    Scan.objects.filter(
                        scan_id=str(y["source"]["attributes"]["last_scan"])
                    ).update(bin_success=False)
                    for y in r["errors"]
                ]

                for y in r["errors"]:
                    this_scan = Scan.objects.get(
                        scan_id=str(y["source"]["attributes"]["last_scan"])
                    )
                    Fail.objects.create(
                        scan=this_scan,
                        batch_id=batch_id,
                        title=y["title"],
                        detail=y["detail"],
                    )

        else:
            process_result = "BIN UNREACHABLE"
            [
                Fail.objects.create(
                    scan=Scan.objects.get(scan_id=x.scan_id),
                    title="Response Error",
                    detail=f"{response.status_code}",
                )
                for x in Scan.objects.filter(batch_id=batch_id)
            ]
        print(process_result)
        return JsonResponse(for_processing["terminal_response"])

    if request.method != "POST":
        return JsonResponse("This is an api endpoint")


@csrf_exempt
@api_view(["GET", "POST"])
def create_scan_api_endpoint(request):
    """
    endpoint for terminal_scan data
    data is processed here, saved to mothership,
    then forwarded to BIN_API_ENDPOINT
    where response is evaluated for success
    and mothership_scan record is updated based on success
    other notes: we are processing all at once at the time of scan upload, should be moved to a task q
    """
    terminal_response_package, bin_package = ({"data": []}, {"data": []})

    if request.method == "POST":
        terminal_post = request.data["data"]
        for scan in terminal_post:

            new_scan, updated = Scan.objects.update_or_create(
                scan_id=scan["id"], defaults=scan["attributes"]
            )

            terminal_response_package["data"].append(
                {
                    "type": "scans",
                    "id": str(new_scan.scan_id),
                    "attributes": {
                        "time_upload": new_scan.time_upload.strftime(
                            "%Y-%m-%dT%H:%M:%S.%f%z"
                        ),
                    },
                }
            )

            bin_package["data"].append(
                {
                    "type": "items",
                    "id": new_scan.tracking,
                    "attributes": {
                        "sku": new_scan.sku,
                        "location": new_scan.readable_location(),
                        "last_scan": str(new_scan.scan_id),
                    },
                }
            )

        def create_and_send(bin_package):
            """
            create and send to bin from list of dicts
            """
            headers = CaseInsensitiveDict()
            headers["Accept"] = "application/json"
            headers["Content-type"] = "application/json"
            headers["Authorization"] = "Bearer {}".format(settings.BIN_KEY)
            payload = json.dumps(bin_package)

            return requests.patch(
                settings.BIN_API_ENDPOINT, data=payload, headers=headers
            )

        def process_for_errors(bin_response):
            """
            eval bin response for errors
            chage scan records based on errors
            """
            if bin_response.status_code == 200:

                if bin_response.json() == {"errors": []}:

                    process_result = "BIN UPDATED WITH NO ERRORS"
                    for x in terminal_post:

                        Scan.objects.filter(scan_id=str(x["id"])).update(
                            bin_success=True
                        )
                        this_scan = Scan.objects.get(scan_id=str(x["id"]))
                        Success.objects.create(scan=this_scan)
                else:
                    process_result = "BIN REACHED WITH ERRORS"
                    r = bin_response.json()
                    [
                        Scan.objects.filter(scan_id=str(x["id"])).update(
                            bin_success=True
                        )
                        for x in terminal_post
                    ]
                    [
                        Scan.objects.filter(
                            scan_id=str(y["source"]["attributes"]["last_scan"])
                        ).update(bin_success=False)
                        for y in r["errors"]
                    ]
                    for y in r["errors"]:
                        this_scan = Scan.objects.get(
                            scan_id=str(y["source"]["attributes"]["last_scan"])
                        )
                        Fail.objects.create(
                            scan=this_scan, title=y["title"], detail=y["detail"]
                        )

            else:
                process_result == "BIN UNREACHABLE"
                for x in terminal_post:
                    this_scan = Scan.objects.get(scan_id=str(x["id"]))
                    Fail.objects.create(
                        scan=this_scan,
                        title="Response Error",
                        detail=f"{bin_response.status_code}",
                    )

            return process_result

        process_for_errors(create_and_send(bin_package, terminal_post))
        return JsonResponse(terminal_response_package)

    elif request.method == "GET":

        return JsonResponse({"errors": ["This endpoint requires POST."]})


@login_required
def export_scans(request):
    date = datetime.datetime.now()

    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="BDDW_SCANS_{date}.csv"'
        },
    )

    writer = csv.writer(response)

    scans = Scan.objects.all().values_list(
        "sku",
        "tracking",
        "location",
        "time_scan",
        "time_upload",
        "scan_id",
        "bin_success",
    )

    writer.writerow(
        [
            "SKU",
            "TRACKING",
            "LOCATION",
            "TIME SCAN",
            "TIME UPLOAD",
            "SCAN ID",
            "BIN SUCCESS",
        ]
    )

    [
        writer.writerow(
            [
                x[0],
                x[1],
                Scan.objects.get(scan_id=x[5]).readable_location(),
                x[3],
                x[4],
                x[5],
                x[6],
            ]
        )
        for x in scans
    ]

    return response


@login_required
def upload_csv(request):

    if request.method == "POST":

        csv_file = request.FILES["file"]
        data_set = csv_file.read().decode("UTF-8")
        io_string = io.StringIO(data_set)
        next(io_string)

        columns = {
            "sku": 0,
            "tracking": 1,
            "location": 2,
            "time_upload": 3,
            "time_scan": 4,
            "scan_id": 5,
            "bin_success": 6,
        }

        for row in csv.reader(io_string, delimiter=",", quotechar='"'):

            loc = settings.LOCATION_CODES
            record = {
                "sku": row[columns["sku"]],
                "tracking": row[columns["tracking"]],
                "location": loc[row[columns["location"]]],
                "time_upload": row[columns["time_upload"]],
                "time_scan": row[columns["time_scan"]],
                "bin_success": row[columns["bin_success"]],
            }

            Scan.objects.update_or_create(
                scan_id=row[columns["scan_id"]], defaults=record
            )

        return HttpResponse("<p>Upload Finished</p>")

    if request.method == "GET":

        return render(request, "upload.html")


@login_required
def export_last_scans(request):
    """
    exports list of records
    if record is latest by tracking number
    """

    date = datetime.datetime.now()

    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="LAST_BY_TRACKING_{date}.csv"'
        },
    )

    writer = csv.writer(response)

    all = Scan.objects.all()

    filtered = [
        [
            scan.sku,
            scan.tracking,
            scan.readable_location(),
            scan.time_scan,
            scan.time_upload,
            scan.scan_id,
            scan.bin_success,
        ]
        for scan in all
        if scan.is_latest() and scan.has_tracking()
    ]

    writer.writerow(
        [
            "SKU",
            "TRACKING",
            "LOCATION",
            "TIME SCAN",
            "TIME UPLOAD",
            "SCAN ID",
            "BIN SUCCESS",
        ]
    )

    [writer.writerow([x[0], x[1], x[2], x[3], x[4], x[5], x[6]]) for x in filtered]

    return response


def bin_api_view(request):

    return render(
        request,
        "api_view.html",
        {
            "scans": Scan.objects.all(),
            "fails": Fail.objects.all(),
            "successes": Success.objects.all(),
        },
    )
