from datetime import datetime

import pytz


def return_unix(datetime_obj):
    ts = (datetime_obj - datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds()
    return ts.__int__().__str__()
