import json
from datetime import datetime

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from scans.models import Scan


class TestScanApi(TestCase):
    def SetUp(self):

        Scan.objects.create(
            sku="39039921",
            tracking="TN-3930901",
            time_scan=datetime.now(),
            location=101,
        )

    def test_all(self):
        all_scans_endpoint = reverse("v2:all")
        response = self.client.get(all_scans_endpoint)

        self.assertIn("39039921", json.loads(response.content))
