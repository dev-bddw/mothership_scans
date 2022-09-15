# mothership scans

This is an internal application for BDDW that can be easily built (local.yml) and deployed (production.yml) with docker.

# features

Exposes a secured API endpoint for recieving data related to BDDW products (identified by SKU numbers) locations or 'SCANS'.

Lists these records securely.

This API endpoint returns a validation UUID. This code identifies scans, can assist with troubleshooting, etc.

For the purposes of this API -- scan records without UUIDs are considered invalid.

# okay api let's get in formation

The API expects the following:
            import requests

            app_key = settings.APP_KEY

            scan_data = {
                "sku": scan.sku,
                "time_scan": scan.time_scan.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
                "tracking": scan.tracking,
                "location": scan.location,
            }

            data_json = json.dumps(scan_data)

            headers = requests.structures.CaseInsensitiveDict()
            headers["Accept"] = "application/json"
            headers["Content-type"] = "application/json"
            headers["Authorization"] = "Token {}".format(app_key)

            response = requests.post(
                "https://bddwscans.com/endpoint/", data=data_json, headers=headers
            )

At this time, you can only send single scans to the endpoint.


# questions

please email lance@bddw.com
