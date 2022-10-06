from django.urls import path

from .views import all

app_name = "v2"

urlpatterns = [path("scans/", view=all, name="all")]
