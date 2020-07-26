import json

import requests
from django.http import JsonResponse
from django.core import exceptions
from django.conf import settings
from pprint import pprint

from group.models import Members

from datetime import timedelta, datetime, timezone

def webhook(request):
    if request.method == 'POST':
        t_data = json.loads(request.body)
        pprint(t_data)

        new_chat_members = t_data.get('message', {}).get('new_chat_members')
        if new_chat_members:
            for new_chat_member in new_chat_members:
                if new_chat_member['id'] != settings.BOT_ID:
                    Members.objects.create(
                        user=new_chat_member['id'],
                        chat=t_data['message']['chat']['id'],
                    )

        left_chat_member = t_data.get('message', {}).get('left_chat_member')
        if left_chat_member:
            Members.objects.filter(user=left_chat_member['id'], chat=t_data['message']['chat']['id']).delete()
            if left_chat_member['id'] == settings.BOT_ID:
                Members.objects.filter(chat=t_data['message']['chat']['id']).delete()

        return JsonResponse({
            'ok': 'POST request processed'
        })
