from django.contrib import admin

from .models import Scan


class ScansAdmin(admin.ModelAdmin):
    search_fields = ["sku", "tracking", "scan_id"]
    list_per_page = 100000


admin.site.register(Scan, ScansAdmin)
