import csv
import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse, render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer

from .models import Scan
from .serializers import ScanSerializer


@login_required
def scans_list(request):

    return render(
        request,
        "scans_list.html",
        {"scans": Scan.objects.all().order_by("-time_upload")},
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
        scans = Scan.objects.filter(sku__startswith=query).order_by("-time_upload")

        if len(scans) == 0:

            scans = Scan.objects.filter(scan_id__startswith=query).order_by(
                "-time_upload"
            )

        return render(request, "partials/search.html", {"scans": scans})


def return_scans_by_sku(request, item_sku):

    order_by = (
        "-time_upload"
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
        "-time_upload"
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
        "-time_upload"
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

    if request.method == "POST":

        jdata = request.data

        serializer = ScanSerializer(data=jdata)

        if serializer.is_valid():

            scan = serializer.create(serializer.data)

            response_message = {
                "success": True,
                "scan_id": scan.scan_id,
                "time_upload": scan.time_upload.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
                "tracking": scan.tracking,
            }

            jdata = JSONRenderer().render(response_message)
            return HttpResponse(jdata, content_type="application/json")

        jdata = JSONRenderer().render(serializer.errors)

        return HttpResponse(jdata, content_type="application/json")


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

    scans = (
        Scan.objects.all()
        .order_by("-time_upload")
        .values_list(
            "sku",
            "tracking",
            "location",
            "time_upload",
            "time_scan",
            "scan_id",
        )
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
