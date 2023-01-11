import json
import random
import uuid

import requests
from django.conf import settings
from django.db import models


class Success(models.Model):

    scan = models.ForeignKey(
        "scans.Scan", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    time = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100, default="Success", blank=True, null=True)
    detail = models.CharField(max_length=500, null=True, blank=True)
    batch_id = models.CharField(max_length=10, default=None, blank=True, null=True)

    class Meta:
        ordering = ["-time"]

    def __str__(self):

        return f"{self.scan}"


class Fail(models.Model):

    scan = models.ForeignKey(
        "scans.Scan", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    time = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=100, default="Fail", blank=True, null=True)
    detail = models.CharField(max_length=500, null=True, blank=True)
    batch_id = models.CharField(max_length=10, default=None, blank=True, null=True)

    class Meta:
        ordering = ["-time"]

    def __str__(self):

        return f"{self.scan}"

    def create_headers(self):
        """
        create request header for bin
        """

        headers = requests.structures.CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Content-type"] = "application/json"
        headers["Authorization"] = "Bearer {}".format(settings.BIN_KEY)
        return headers

    def resend(self):
        """
        resend scan data to bin for this fail.
        update scan record if resend succeeds.
        create success record for scan.
        """
        headers = self.create_headers()

        data = {
            "data": [
                {
                    "type": "items",
                    "id": self.scan.tracking,
                    "attributes": {
                        "sku": self.scan.sku,
                        "location": self.scan.readable_location(),
                        "last_scan": str(self.scan.scan_id),
                    },
                }
            ]
        }

        response = requests.patch(
            settings.BIN_API_ENDPOINT,
            data=json.dumps(data),
            headers=headers,
        )

        if response.json() == {"errors": []}:

            self.scan.bin_success = True
            self.title = "RESOLVED"
            self.detail = "Success after resend"
            self.scan.save()
            self.save()
            batch_id = random.randint(0, 10000)
            Success.objects.create(scan=self.scan, batch_id=batch_id)
            return True

        elif response.json() != {"errors": []} and response.status_code == 200:
            error_response = response.json()["errors"][0]
            self.title = error_response["title"]
            self.detail = error_response["detail"]
            self.save()

            return False

        else:
            self.title = "RESPONSE ERROR"
            self.details = response.status_code
            self.save()
            return False


class Scan(models.Model):

    sku = models.CharField(blank=False, null=False, max_length=200)

    tracking = models.CharField(blank=True, null=True, max_length=200)

    time_scan = models.DateTimeField()

    scan_id = models.UUIDField(default=uuid.uuid4)

    location = models.IntegerField()
    time_upload = models.DateTimeField(auto_now_add=True)

    bin_success = models.BooleanField(default=False)

    batch_id = models.CharField(max_length=10, default=None, blank=True, null=True)

    class Meta:
        ordering = ["-time_scan"]

    def __str__(self):
        return f"SKU: {self.sku} LOC: {self.location} UID: {self.scan_id}"

    def readable_location(self):
        """
        RETURNS BIN READABLE LOCATION
        TODO: rename to something that make sense
        """
        locations = {
            "301": "FRANKFORD",
            "201": "RED LION",
            "101": "TEST",
            "401": "ERIE",
            "501": "NEW YORK",
            "601": "LONDON - MOUNT",
            "602": "LONDON - VYNER",
        }

        return locations[str(self.location)]

    def has_tracking(self):
        return self.tracking not in [None, "", " "]

    def is_latest(self):
        return Scan.objects.filter(tracking=self.tracking).first() == self
