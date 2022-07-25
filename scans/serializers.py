from rest_framework import serializers

from .models import Scan


class ScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scan
        fields = ["sku", "tracking", "time_scan", "location"]

    def create(self, validated_data):
        return Scan.objects.create(**validated_data)
