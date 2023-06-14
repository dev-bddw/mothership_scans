# noqa
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views

from frontend.views import search_entry
from scans.views import failed_list
from scans.views_api import create_scan_api_endpoint_v3
from scans.views_csv import export_fails, export_last_scans, upload_csv
from scans.views_hx import resend_scan_hx

# THE ONE API ENDPOINT FOR THIS APP
urlpatterns = [
    path("endpoint/", view=create_scan_api_endpoint_v3, name="endpoint"),
]

# OTHER COMMON VIEWS
urlpatterns += [
    path("", view=search_entry, name="home"),
    path("frontend/", include("frontend.urls", namespace="frontend")),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("accounts/", include("allauth.urls")),
    # Your stuff: custom urls includes go here
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# OLD - DEPERECATED????
urlpatterns += [
    path("resend/<pk>", view=resend_scan_hx, name="resend"),
    path("failed-scans/", view=failed_list, name="failed-list"),
]


# CSV URLS
urlpatterns += [
    path("csv/export-fails/", view=export_fails, name="export-fails"),
    path("csv/uploads/", view=upload_csv, name="upload"),
    path("csv/export-latest/", view=export_last_scans, name="export-latest"),
]


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
