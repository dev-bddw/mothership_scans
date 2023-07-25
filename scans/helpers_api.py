import json
import random

import requests
from django.conf import settings
from requests.structures import CaseInsensitiveDict

from .models import Fail, Scan, Success
from .time_convert import return_unix


def process_scans(request):

    batch_id = random.randint(0, 100000000)

    for_processing = {
        "batch_id": batch_id,
        "data_from_terminal": request.data["data"],
        "terminal_response": {"data": []},
        "bin_request_body": {"data": []},
    }

    def create_scans():
        """step one: convert terminal data to scan records"""
        for scan in for_processing["data_from_terminal"]:
            # changed to update_or_create to prevent two scans with same scan_id
            defaults = scan["attributes"]
            defaults.update({"batch_id": batch_id, "scan_id": scan["id"]})

            try:
                existing = Scan.objects.get(scan_id=scan["id"])
                existing.batch_id = batch_id
                existing.save()

                continue
                # if you find a scan matching this scan id, do nothing

            except Scan.DoesNotExist:
                # create the scan record
                ############################################################
                Scan.objects.update_or_create(**defaults)
                ############################################################
                continue

            except Scan.MultipleObjectsReturned:
                # multiple scans with same id is a big error and causes problems for this thing
                # and because the terminal is expectina  response for each scan id -- we can't just
                # ignore the scan if the scan_id exists already
                # so we are going to remove all the scans that are already in there, then create a fresh one
                Scan.objects.filter(scan_id=scan["id"]).delete()
                Scan.objects.update_or_create(**defaults)

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
        print("sending to the bin:")
        print(json.dumps(for_processing["bin_request_body"]))

        response = requests.patch(
            settings.BIN_API_ENDPOINT,
            data=json.dumps(for_processing["bin_request_body"]),
            headers=headers,
        )

        # handle result

        if response.status_code == 200:

            try:
                # turn the response body (stringified json) into a python dictionary
                bin_response = response.json()

                if bin_response == {"errors": []}:

                    # bin says everything updated correctly
                    process_result = "BIN UPDATED WITH NO ERRORS"

                    # mark everything a success
                    Scan.objects.filter(batch_id=batch_id).update(bin_success=True)

                    # create success objects quick
                    [
                        Success.objects.create(scan=x, batch_id=batch_id)
                        for x in Scan.objects.filter(batch_id=batch_id)
                    ]

                else:

                    process_result = "BIN REACHED WITH ERRORS"

                    # mark all the  scan success (first)
                    Scan.objects.filter(batch_id=batch_id).update(bin_success=True)

                    # then go back through and marked the ones failed that failed
                    [
                        Scan.objects.filter(
                            scan_id=str(y["source"]["attributes"]["scan_id"])
                        ).update(bin_success=False)
                        for y in bin_response["errors"]
                    ]

                    # and now create Fail records for the failed scans
                    for y in bin_response["errors"]:
                        # for each error in the error response lookup the failed scan by ID
                        # that comes back from the bin
                        this_scan = Scan.objects.filter(
                            scan_id=str(y["source"]["attributes"]["scan_id"])
                        ).first()

                        # create a failed scan record, fk to the scan itself
                        Fail.objects.create(
                            scan=this_scan,
                            batch_id=batch_id,
                            title=y["title"],
                            detail=y["detail"],
                        )

            except json.JSONDecodeError:
                # the bin responded, but it wasnt wasn't valid json
                process_result = "THERE WAS AS ERROR DECODING THE BIN RESPONSE."
                # we have to assume the scans failed
                Scan.objects.filter(batch_id=batch_id).update(bin_success=False)
                # create fail records
                [
                    Fail.objects.create(
                        scan=x,
                        batch_id=batch_id,
                        title="DECODE ERROR",
                        detail=process_result,
                    )
                    for x in Scan.objects.filter(batch_id=batch_id)
                ]

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
