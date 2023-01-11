# bin patch request to update items

request_body = {
    "data": [
        {
            "type": "items",
            "id": "TN-000000000",
            "attributes": {
                "sku": "220520000",
                "location": "RED LION",
                "last_scan": "3c9fc216-4fe0-44f9-9774-ebc88b7d8171",
            },
        }
    ]
}

# successful response

response = {"errors": []}

# reached but with errors
# two errors possible right now 011023
# tracking number not found
# tracking number improperly formatted
response = {
    "errors": [
        {
            "code": "FAILED",
            "detail": "Tracking number not found",
            "id": "TN-2929181",
            "title": "An error occured with this tracking number",
            "source": {
                # returns exact copy of dict sent
                "type": "items",
                "id": "TN-2929181",
                "attributes": {
                    "sku": "220520000",
                    "location": "RED LION",
                    "last_scan": "b478b326-3147-49c2-944b-773a0bd0f902",
                },
            },
        }
    ]
}
