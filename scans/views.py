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
    in dev
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


def resend_scan_hx(request, pk):
    """
    resend failed scan to bin
    """

    result = Fail.objects.get(id=pk).resend()

    in_template = "Success" if result else "Failed"

    return HttpResponse(in_template)


@csrf_exempt
@api_view(["POST"])
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
        print(json.dumps(for_processing["bin_request_body"]))
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


@login_required
def export_fails(request):
    """
    exports fail data to csv after using fk relation
    to grab pertinent scan data
    """

    date = datetime.datetime.now()

    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="BDDW_FAILS_{date}.csv"'
        },
    )

    writer = csv.writer(response)

    fails = Fail.objects.all().values_list(
        "scan",
        "time",
        "title",
        "detail",
        "batch_id",
    )

    combine_scan_data = [
        [
            Scan.objects.get(id=x[0]).scan_id,
            Scan.objects.get(id=x[0]).tracking,
            Scan.objects.get(id=x[0]).time_scan,
            Scan.objects.get(id=x[0]).readable_location(),
            Scan.objects.get(id=x[0]).sku,
            Scan.objects.get(id=x[0]).bin_success,
            x[1],
            x[2],
            x[3],
            x[4],
        ]
        for x in fails
    ]

    writer.writerow(
        [
            "SCAN ID",
            "TRACKING",
            "TIME SCAN",
            "LOCATION",
            "SKU",
            "BIN SUCCESS",
            "TIME FAIL",
            "FAIL TITLE",
            "FAIL DETAIL",
            "BATCH ID",
        ]
    )

    for row in combine_scan_data:
        writer.writerow(row)

    return response


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
        "failed_list.html",
        {
            "scans": Scan.objects.all(),
            "fails": Fail.objects.all(),
            "successes": Success.objects.all(),
        },
    )
