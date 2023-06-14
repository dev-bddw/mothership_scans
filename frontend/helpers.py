import json

from rest_framework.authtoken.models import Token

from scans.models import Scan


def return_context(request):
    """context for initial search/list view"""

    def get_scans():
        """return all scans"""
        return [x.to_dict() for x in Scan.objects.all().order_by("-time_scan")]

    def get_or_create_token():
        """
        if user, return token (or create one)
        else return none
        """
        user = request.user if request.user.is_authenticated else None

        if user is not None:
            try:
                token = Token.objects.get(user=user)
            except Token.DoesNotExist:
                token = Token.objects.create(user=user)
            return token.key
        else:
            return None

    return json.dumps(
        {
            "auth_token": get_or_create_token(),
            "scans": get_scans(),
        }
    )


def return_search_results(query):
    """match query to scans"""

    matching_scans = []

    def match_all_scans():
        """return all scans"""
        for obj in Scan.objects.all().order_by("-time_scan"):
            matching_scans.append(
                obj.to_dict()
            ) if obj.to_dict() not in matching_scans else None

    def match_sku():
        """match by sku"""
        for obj in Scan.objects.filter(sku__icontains=query):
            matching_scans.append(
                obj.to_dict()
            ) if obj.to_dict() not in matching_scans else None

    def match_tracking():
        """match by tracking number"""
        for obj in Scan.objects.filter(tracking__icontains=query):
            matching_scans.append(
                obj.to_dict()
            ) if obj.to_dict() not in matching_scans else None

    def match_scan_id():
        """match scan_id"""
        for obj in Scan.objects.filter(scan_id__icontains=query):
            matching_scans.append(
                obj.to_dict()
            ) if obj.to_dict() not in matching_scans else None

    def match_location():
        """match location"""
        location_key = lookup_location_code(query)
        for obj in Scan.objects.filter(location=location_key):
            matching_scans.append(
                obj.to_dict()
            ) if obj.to_dict() not in matching_scans else None

    if query != " " and query != "":
        """if didn't recieve empty query, search"""
        match_sku()
        match_tracking()
        match_scan_id()
        match_location()

    else:
        """if query was empty, just return all scans"""
        match_all_scans()

    return matching_scans


def lookup_location_code(name):
    """reverse lookup of name of location and returns location code"""
    locations = {
        "301": "FRANKFORD",
        "201": "RED LION",
        "101": "TEST",
        "401": "ERIE",
        "501": "NEW YORK",
        "601": "LONDON - MOUNT",
        "602": "LONDON - VYNER",
    }

    if name in locations.values():
        for (key, value) in locations.items():
            if name == value:
                return key
    else:
        return 000
