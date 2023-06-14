from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from .models import Fail, PageNote, Scan


@login_required
def search_scans_hx(request):
    """
    HX view for basic search
    uuids are lower case
    skus sometimes have characters that are case sensitive
    TODO: use icontains or istarswith for insensitive
    """
    if request.method == "POST":

        query = request.POST.get("search")

        lll = []

        def x_not_in_lll(x, lll=lll):

            if [
                x.sku,
                x.tracking,
                x.location,
                x.time_scan,
                x.time_upload,
                x.scan_id,
                x.bin_success,
            ] not in lll:
                return True

            else:
                return False

        [
            lll.append(
                [
                    x.sku,
                    x.tracking,
                    x.location,
                    x.time_scan,
                    x.time_upload,
                    x.scan_id,
                    x.bin_success,
                ]
            )
            for x in Scan.objects.filter(sku__startswith=query.upper())
            if x_not_in_lll(x)
        ]
        [
            lll.append(
                [
                    x.sku,
                    x.tracking,
                    x.location,
                    x.time_scan,
                    x.time_upload,
                    x.scan_id,
                    x.bin_success,
                ]
            )
            for x in Scan.objects.filter(tracking__contains=query.upper())
            if x_not_in_lll(x)
        ]
        [
            lll.append(
                [
                    x.sku,
                    x.tracking,
                    x.location,
                    x.time_scan,
                    x.time_upload,
                    x.scan_id,
                    x.bin_success,
                ]
            )
            for x in Scan.objects.filter(scan_id__startswith=query.lower())
            if x_not_in_lll(x)
        ]

        lll.sort(reverse=True, key=lambda s: s[3])
        scans = [
            {
                "sku": y[0],
                "tracking": y[1],
                "location": y[2],
                "time_scan": y[3],
                "time_upload": y[4],
                "scan_id": y[5],
                "bin_success": y[6],
            }
            for y in lll
        ]

        return render(request, "scans/partials/search.html", {"scans": scans})

    else:

        return HttpResponse("this endpoint accepts post only")


@login_required
def resend_scan_hx(request, pk):
    """
    resend failed scan to bin
    """

    result = Fail.objects.get(id=pk).resend()

    in_template = "Success" if result else "Failed"

    return HttpResponse(in_template)


@login_required
def note_hx(request):

    if request.POST["note"]:
        try:
            txt = PageNote.objects.filter(page="front page").update(
                note=request.POST["note"]
            )
        except PageNote.DoesNotExist:
            txt = "error"

        return HttpResponse(txt)

    else:

        return HttpResponse("must be post request")
