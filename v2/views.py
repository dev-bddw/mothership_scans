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

        response = {"data": None}

    json_response = JsonResponse(response, safe=False)
    json_response.headers["Access-Control-Allow-Origin"] = "*"

    print(print(json_response.headers))

    return json_response
