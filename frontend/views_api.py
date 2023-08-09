from django.http import JsonResponse
from rest_framework.decorators import api_view

from .helpers import return_search_results


# DEPRECATED
@api_view(["POST"])
def search_api(request):
    """
    handles search queries
    """
    data = request.data["data"]["search"]

    results = return_search_results(data)

    return JsonResponse({"data": results})
