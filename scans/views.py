from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Fail, PageNote, Scan, Success


@login_required
def scans_list(request):

    try:
        note = PageNote.objects.get(page="front page").note
    except PageNote.DoesNotExist:
        note = "Please create a PageNote w/ page = 'front page' "
    return render(
        request,
        "scans_list.html",
        {
            "scans": Scan.objects.all(),
            "note": note,
        },
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


@login_required
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


@login_required
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
def failed_list(request):

    return render(
        request,
        "failed_list.html",
        {
            "scans": Scan.objects.all(),
            "fails": Fail.objects.all(),
            "successes": Success.objects.all(),
        },
    )
