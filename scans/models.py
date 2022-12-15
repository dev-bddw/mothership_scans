import uuid

from django.db import models


class Scan(models.Model):

    sku = models.CharField(blank=False, null=False, max_length=200)

    tracking = models.CharField(blank=True, null=True, max_length=200)

    time_scan = models.DateTimeField()

    scan_id = models.UUIDField(default=uuid.uuid4)

    location = models.IntegerField()
    time_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-time_scan"]

    def __str__(self):
        return f"SKU: {self.sku} LOC: {self.location} UID: {self.scan_id}"

    def is_latest(self):

        if self.tracking in [None, ""]:

            return Scan.objects.filter(sku=self.sku).first() == self

        else:

            return Scan.objects.filter(tracking=self.tracking).first() == self
