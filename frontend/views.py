from django.shortcuts import render
from rest_framework.decorators import api_view

from .helpers import return_context


def search_entry(request):
    """
    kick off the search
    """
    context = return_context(request)

    return render(request, "frontend/search/dist/index.html", {"context": context})
