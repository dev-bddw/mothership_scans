import csv
import datetime
import io

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from .models import Fail, Scan


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
    """
    deprecated
    """

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

    def handle_return_readable(scan_id):
        """
        handle case where multiple scans show up with same scan_id
        not sure why this is happening
        """
        try:
            Scan.objects.get(scan_id=scan_id).readable_location(),
        except Scan.MultipleObjectsReturned:
            print("this scan raised a multiple objects returned exception")
            for scan in Scan.objects.filter(scan_id=scan_id):
                if scan.is_latest():
                    return scan.readable_location()
                else:
                    return "THis is a duplicate"

    [
        writer.writerow(
            [
                x[0],
                x[1],
                handle_return_readable(x[5]),
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
