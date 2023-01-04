import csv
import datetime
import io
import json

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from requests.structures import CaseInsensitiveDict
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer

from .models import Scan
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

    if request.method == "POST":

        terminal_data = request.data

        terminal_response_package = {"data": []}
        bin_package = {"data": []}

        for scan in terminal_data["data"]:

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
                    "id": new_scan.tracking.split("-")[1],
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
                    [
                        Scan.objects.filter(scan_id=str(x["id"])).update(
                            bin_success=True
                        )
                        for x in terminal_data["data"]
                    ]
                else:
                    r = bin_response.json()
                    for x in r["errors"]:
                        terminal_data["data"].remove(x["attributes"]["source"])
                        [
                            Scan.objects.filter(scan_id=str(x["id"])).update(
                                bin_success=True
                            )
                            for x in terminal_data["data"]
                        ]

                return bin_response

        # process_for_errors(create_and_send(bin_package))

        return JsonResponse(terminal_response_package)

    else:

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
    )
    writer.writerow(
        ["SKU", "TRACKING", "LOCATION", "TIME SCAN", "TIME UPLOAD", "SCAN ID"]
    )

    loc = {
        "301": "FRANKFORD",
        "201": "RED LION",
        "101": "TEST",
        "401": "ERIE",
        "501": "NEW YORK",
        "601": "LONDON - MOUNT",
        "602": "LONDON - VYNER",
    }

    for record in scans:
        record = list(record)
        record[2] = loc.get(str(record[2]))

        writer.writerow(record)

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
        }

        for row in csv.reader(io_string, delimiter=",", quotechar='"'):

            loc = {
                "FRANKFORD": 301,
                "RED LION": 201,
                "TEST": 101,
                "ERIE": 401,
                "NEW YORK": 501,
                "LONDON - MOUNT": 601,
                "LONDON - VYNER": 602,
            }

            record = {
                "sku": row[columns["sku"]],
                "tracking": row[columns["tracking"]],
                "location": loc[row[columns["location"]]],
                "time_upload": row[columns["time_upload"]],
                "time_scan": row[columns["time_scan"]],
                # 'scan_id': row[columns['scan_id']],
            }

            Scan.objects.update_or_create(
                scan_id=row[columns["scan_id"]], defaults=record
            )

        return HttpResponse("<p>Upload Finished</p>")

    if request.method == "GET":

        return render(request, "upload.html")


@login_required
def export_last_scans(request):
    date = datetime.datetime.now()

    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="BDDW_SCANS_{date}.csv"'
        },
    )

    writer = csv.writer(response)

    all = Scan.objects.all()

    filtered = []

    for s in all:

        if s.is_latest():

            filtered.append(s)

    tm = [
        [x.sku, x.tracking, x.location, x.time_scan, x.time_upload, x.scan_id]
        for x in filtered
    ]

    writer.writerow(
        ["SKU", "TRACKING", "LOCATION", "TIME SCAN", "TIME UPLOAD", "SCAN ID"]
    )

    loc = {
        "301": "FRANKFORD",
        "201": "RED LION",
        "101": "TEST",
        "401": "ERIE",
        "501": "NEW YORK",
        "601": "LONDON - MOUNT",
        "602": "LONDON - VYNER",
    }

    for record in tm:

        record[2] = loc.get(str(record[2]))

        writer.writerow(record)

    return response
