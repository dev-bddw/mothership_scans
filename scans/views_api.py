from django.http import JsonResponse
from rest_framework.decorators import api_view

from .helpers_api import process_scans


@api_view(["POST"])
def create_scan_api_endpoint_v3(request):
    """
    create scans
    update bin
    record bin response
    return response to terminal
    """
    response = process_scans(request)
    return JsonResponse(response)
