from django.shortcuts import HttpResponse, render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer

from .models import Scan
from .serializers import ScanSerializer


# Create your views here.
def scans_list(request):

    return render(request, "scans_list.html", {"scans": Scan.objects.all()})


@csrf_exempt
@api_view(["GET", "POST"])
def create_scan_api_endpoint(request):

    if request.method == "POST":

        jdata = request.data

        serializer = ScanSerializer(data=jdata)

        if serializer.is_valid():

            scan = serializer.create(serializer.data)

            response_message = {
                "Success": True,
                "UUID": scan.scan_id,
                "time uploaded": "TBI",
            }

            jdata = JSONRenderer().render(response_message)
            return HttpResponse(jdata, content_type="application/json")

        jdata = JSONRenderer().render(serializer.errors)

        return HttpResponse(jdata, content_type="application/json")
