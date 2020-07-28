import json

from django.http import JsonResponse
from pprint import pprint

from group.models import Blacklist, Gratitudes, Groups, Info, Members, Swearing

from time import mktime

from django.utils import timezone
from group.telegram_bot_api import API

import re
from group import urlmarker
import functools


def custom_search(iterable, obj):
    for element in iterable:
        if element in obj:
            return True
    return False





def webhook(request):
    if request.method == 'POST':
        t_data = json.loads(request.body)
        pprint(t_data)
        return JsonResponse({
            'ok': True,
        })

