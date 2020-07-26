import json

import requests
from django.http import JsonResponse
from django.core import exceptions
from django.conf import settings
from pprint import pprint

from group.models import Members

from datetime import timedelta, datetime, timezone

def check_messages_from_new_members(t_data):
    try:
        user_date_joined = Members.objects.get(
            user=t_data.get('message', {}).get('from', {}).get('id'),
            chat=t_data.get('message', {}).get('chat', {}).get('id')
        ).date_joined
    except exceptions.ObjectDoesNotExist:
        return

    entities = t_data.get('message', {}).get('entities', [])

    is_user_new = (datetime.now(timezone.utc) - user_date_joined) < timedelta(days=2)
    has_message_url = any([entity.get('type') == 'url' for entity in entities])
    has_message_mention = any([entity.get('type') == 'mention' for entity in entities])

    if (has_message_url or has_message_mention) and is_user_new:
        data = {
            'chat_id': t_data['message']['chat']['id'],
            'message_id': t_data['message']['message_id'],
        }
        requests.post(f'https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/deleteMessage', data=data)


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
                data = {
                    'chat_id': t_data['message']['chat']['id'],
                    'message_id': t_data['message']['message_id'],
                }
                requests.post(f'https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/deleteMessage', data=data)

        left_chat_member = t_data.get('message', {}).get('left_chat_member')
        if left_chat_member:
            Members.objects.filter(user=left_chat_member['id'], chat=t_data['message']['chat']['id']).delete()
            if left_chat_member['id'] == settings.BOT_ID:
                Members.objects.filter(chat=t_data['message']['chat']['id']).delete()

        check_messages_from_new_members(t_data)

        return JsonResponse({
            'ok': 'POST request processed'
        })
