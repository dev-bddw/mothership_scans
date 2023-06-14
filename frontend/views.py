from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .helpers import return_context


@login_required
def search_entry(request):
    """
    kick off the search
    """
    context = return_context(request)

    return render(request, "frontend/search/dist/index.html", {"context": context})
