import json

from django.http import JsonResponse

from scans.models import Scan


def all(request):

    if request.GET.get("sku"):

        q_set = Scan.objects.filter(sku=request.GET.get("sku"))

    else:

        q_set = Scan.objects.all()

    response = {
        "data": [
            {
                "type": "scans",
                "id": s.scan_id if s.scan_id else "",
                "attributes": {
                    "sku": s.sku,
                    "tracking": s.tracking,
                    "time_scan": s.time_scan,
                    "location": str(s.location),
                    "time_upload": s.time_upload,
                },
            }
            for s in q_set
        ]
    }

    if len(response["data"]) < 1:

        response = {
            "data": [
                {
                    "type": "scans",
                    "id": None,
                    "attributes": {
                        "sku": None,
                        "tracking": None,
                        "time_scan": None,
                        "location": None,
                        "time_upload": None,
                    },
                }
            ]
        }

    return JsonResponse(response, safe=False)
