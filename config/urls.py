from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from rest_framework.authtoken.views import obtain_auth_token

from scans.views import (  # create_scan_api_endpoint_v2,
    create_scan_api_endpoint_v3,
    export_fails,
    export_last_scans,
    export_scans,
    failed_list,
    note_hx,
    resend_scan_hx,
    return_scans_by_location,
    return_scans_by_sku,
    return_scans_by_tn,
    scans_list,
    scans_sorting,
    search_scans,
    upload_csv,
)

# API URLS
urlpatterns = [
    path("endpoint/", view=create_scan_api_endpoint_v3, name="endpoint"),
]

# OTHER URLS
urlpatterns += [
    path("", view=scans_list, name="home"),
    path("resend/<pk>", view=resend_scan_hx, name="resend"),
    path("sort/", view=scans_sorting, name="sorting"),
    path("search/", view=search_scans, name="search"),
    path("note/", view=note_hx, name="note_hx"),
    path("by-sku/<item_sku>/", view=return_scans_by_sku, name="by-sku"),
    path(
        "by-location/<int:location>/", view=return_scans_by_location, name="by-location"
    ),
    path("by-tn/<tn>/", view=return_scans_by_tn, name="by-tn"),
    path("failed-scans/", view=failed_list, name="failed-list"),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("accounts/", include("allauth.urls")),
    # Your stuff: custom urls includes go here
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# CSV URLS
urlpatterns += [
    path("csv/export-scans/", view=export_scans, name="export-scans"),  # deprecated
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
