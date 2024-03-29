import json
import random
import uuid

import pytz
import requests
from django.conf import settings
from django.db import models


def convert_eastern(utc_time):
    """convert utc time to est"""
    EST = pytz.timezone("US/Eastern")
    est_time = utc_time.astimezone(EST)
    return est_time.strftime("%b %d %Y, %I:%M %p")


class Success(models.Model):

    scan = models.ForeignKey(
        "scans.Scan", on_delete=models.CASCADE, blank=True, null=True
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
        "scans.Scan", on_delete=models.CASCADE, blank=True, null=True
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
        from .time_convert import return_unix

        data = {
            "data": [
                {
                    "type": "items",
                    "id": self.scan.tracking,
                    "attributes": {
                        "sku": self.scan.sku,
                        "location": self.scan.readable_location(),
                        "scan_id": self.scan.scan_id.__str__(),
                        "time_scan": return_unix(self.scan.time_scan),
                    },
                }
            ]
        }

        response = requests.patch(
            settings.BIN_API_ENDPOINT,
            data=json.dumps(data),
            headers=headers,
        )

        if response.status_code == 200:

            if response.json() == {"errors": []}:

                self.scan.bin_success = True
                self.title = "RESOLVED"
                self.detail = "Success after resend"
                self.scan.save()
                self.save()
                batch_id = random.randint(0, 10000)
                Success.objects.create(scan=self.scan, batch_id=batch_id)
                return True

            elif response.json() != {"errors": []}:
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
        return f"<{self.batch_id}::{self.time_scan}::{self.tracking}::{self.scan_id}>"

    def readable_location(self):
        """
        RETURNS BIN READABLE LOCATION
        """
        locations = {
            "301": "FRANKFORD",
            "201": "RED LION",
            "101": "TEST",
            "401": "ERIE",
            "501": "NEW YORK",
            "601": "LONDON - MOUNT",
            "602": "LONDON - VYNER",
            "701": "LA",
        }

        return locations[str(self.location)]

    def to_dict(self):
        """
        return diction list for this model to be used
        """
        return {
            "id": self.id,
            "sku": self.sku,
            "tracking": self.tracking,
            "time_scan": convert_eastern(self.time_scan),
            "scan_id": self.scan_id.__str__(),
            "location": self.readable_location(),
            "time_upload": convert_eastern(self.time_upload),
            "bin_success": self.bin_success,
            "batch_id": self.batch_id,
        }

    def has_tracking(self):
        return self.tracking not in [None, "", " "]

    def is_latest(self):
        return Scan.objects.filter(tracking=self.tracking).first() == self


class PageNote(models.Model):

    note = models.TextField(max_length=10000, null=True, blank=True)
    page = models.CharField(max_length=100, null=True, blank=True)
