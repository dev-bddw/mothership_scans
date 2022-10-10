from django.urls import path

from .views import all, by_sku

app_name = "v2"

urlpatterns = [
    path("scans/", view=all, name="all"),
    path("scans/<sku>/", view=by_sku, name="by-sku"),
]
