from django.urls import path

from .views import search_entry
from .views_api import search_api

app_name = "frontend"

# ENTRY
urlpatterns = [path("", view=search_entry, name="search")]

urlpatterns += [path("api/", view=search_api, name="search_api")]
