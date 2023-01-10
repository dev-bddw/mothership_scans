from django.contrib import admin

from .models import Fail, Scan, Success


class SuccessAdmin(admin.ModelAdmin):
    search_fields = ["scan__sku", "scan__tracking", "scan__scan_id"]
    list_per_page = 100000


class FailAdmin(admin.ModelAdmin):
    search_fields = ["scan__sku", "scan__tracking", "scan__scan_id"]
    list_per_page = 100000


class ScansAdmin(admin.ModelAdmin):
    search_fields = ["sku", "tracking", "scan_id"]
    list_per_page = 100000


admin.site.register(Fail, FailAdmin)
admin.site.register(Success, SuccessAdmin)
admin.site.register(Scan, ScansAdmin)
