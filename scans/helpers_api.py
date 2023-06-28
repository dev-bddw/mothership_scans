import json
import random

import requests
from django.conf import settings
from requests.structures import CaseInsensitiveDict

from .models import Fail, Scan, Success
from .time_convert import return_unix


def process_scans(request):

    batch_id = random.randint(0, 10000)

    for_processing = {
        "batch_id": batch_id,
        "data_from_terminal": request.data["data"],
        "terminal_response": {"data": []},
        "bin_request_body": {"data": []},
    }

    def create_scans():
        """step one: convert terminal data to scan records"""
        for scan in for_processing["data_from_terminal"]:
            try:
                defaults = scan["attributes"]
                defaults.update({"batch_id": batch_id, "scan_id": scan["id"]})
                Scan(**defaults).save()
            except ValueError:
                continue

    def create_terminal_response():
        """step two: create terminal response from scans with this batch id"""
        for scan in Scan.objects.filter(batch_id=batch_id):
            try:
                for_processing["terminal_response"]["data"].append(
                    {
                        "type": "scans",
                        "id": str(scan.scan_id),
                        "attributes": {"time_upload": scan.time_upload.__str__()},
                    }
                )
            except ValueError:
                continue

    def create_bin_request_body():
        """step three: prepare request body for bin api call"""
        for scan in Scan.objects.filter(batch_id=batch_id):
            try:
                for_processing["bin_request_body"]["data"].append(
                    {
                        "type": "items",
                        "id": scan.tracking,
                        "attributes": {
                            "sku": scan.sku,
                            "location": scan.readable_location(),
                            "scan_id": scan.scan_id.__str__(),
                            "time_scan": return_unix(scan.time_scan),
                        },
                    }
                )

            except ValueError:
                continue

    def send_to_bin():
        """step four: send the request to the bin and process response"""

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

        # handle result

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
                        scan_id=str(y["source"]["attributes"]["scan_id"])
                    ).update(bin_success=False)
                    for y in r["errors"]
                ]

                for y in r["errors"]:
                    this_scan = Scan.objects.get(
                        scan_id=str(y["source"]["attributes"]["scan_id"])
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

    create_scans()
    create_terminal_response()
    create_bin_request_body()
    send_to_bin()

    return for_processing["terminal_response"]
