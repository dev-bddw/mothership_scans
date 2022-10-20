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

    return render(
        request,
        "scans_list.html",
        {"scans": Scan.objects.filter(sku=item_sku).order_by("-time_upload")},
    )


def return_scans_by_tn(request, tn):

    return render(
        request,
        "scans_list.html",
        {"scans": Scan.objects.filter(tracking=tn).order_by("-time_upload")},
    )


def return_scans_by_location(request, location):

    return render(
        request,
        "scans_list.html",
        {"scans": Scan.objects.filter(location=location).order_by("-time_upload")},
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
