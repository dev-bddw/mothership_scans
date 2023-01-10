import uuid

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
    time = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100, default="Fail", blank=True, null=True)
    detail = models.CharField(max_length=500, null=True, blank=True)
    batch_id = models.CharField(max_length=10, default=None, blank=True, null=True)

    class Meta:
        ordering = ["-time"]

    def __str__(self):

        return f"{self.scan}"


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
