from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token

from scans.views import (
    create_scan_api_endpoint,
    return_scans_by_location,
    return_scans_by_sku,
    return_scans_by_tn,
    scans_list,
    scans_sorting,
    search_scans,
)

urlpatterns = [
    path("", view=scans_list, name="home"),
    path("v2/", include("v2.urls", namespace="v2")),
    path("endpoint/", view=create_scan_api_endpoint, name="endpoint"),
    path("sort/", view=scans_sorting, name="sorting"),
    path("search/", view=search_scans, name="search"),
    path("by-sku/<item_sku>/", view=return_scans_by_sku, name="by-sku"),
    path(
        "by-location/<int:location>/", view=return_scans_by_location, name="by-location"
    ),
    path("by-tn/<tn>/", view=return_scans_by_tn, name="by-tn"),
    path(
        "about/", TemplateView.as_view(template_name="pages/about.html"), name="about"
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("mothership_scans.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    # Your stuff: custom urls includes go here
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# API URLS
urlpatterns += [
    # API base url
    path("api/", include("config.api_router")),
    # DRF auth token
    path("auth-token/", obtain_auth_token),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
]

# # SILKY
# urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]


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
