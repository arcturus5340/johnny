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


def is_member(func):
    @functools.wraps(func)
    def wrapper(chat_obj, user_obj):
        admins = API.getChatAdministrators(chat_obj['id']).get('result', [])
        is_admin = user_obj['id'] in (admin_data['user']['id'] for admin_data in admins)
        if not is_admin:
            func(chat_obj, user_obj)
    return wrapper


@is_member
def mute_user(chat_obj, user_obj):
    user, _ = Members.objects.get_or_create(
        id=user_obj['id'],
        username=user_obj['first_name'],
    )
    info, _ = Info.objects.get_or_create(
        user=user,
        chat=Groups.objects.get(id=chat_obj['id']),
        defaults={
            'date_joined': timezone.now() - timezone.timedelta(days=2),
        }
    )
    info.mute_rating += 1
    info.save()
    if info.mute_rating == 1:
        until_date = int(mktime((timezone.now() + timezone.timedelta(hours=6)).timetuple()))
        text = '{} перемещен в карантин на 6 часов за первое нарушение.'.format(user_obj['first_name'])
        API.sendMessage(chat_obj['id'], text)
    elif info.mute_rating == 2:
        until_date = int(mktime((timezone.now() + timezone.timedelta(hours=12)).timetuple()))
        text = '{} перемещен в карантин на 12 часов за второе нарушение.'.format(user_obj['first_name'])
        API.sendMessage(chat_obj['id'], text)
    elif info.mute_rating == 3:
        until_date = int(mktime((timezone.now() + timezone.timedelta(hours=24)).timetuple()))
        text = '{} перемещен в карантин на 24 часа за третье нарушение.'.format(user_obj['first_name'])
        API.sendMessage(chat_obj['id'], text)
    else:
        text = '{} удален из чата за четвертое нарушение.'.format(user_obj['first_name'])
        API.sendMessage(chat_obj['id'], text)
        API.kickChatMember(
            chat_obj['id'],
            user_obj['id']
        )
        Info.objects.filter(
            user=user,
            chat=Groups.objects.get(
                id=chat_obj['id'],
            ),
        ).delete()
        return JsonResponse({
            'ok': True,
        })

    data = {
        'chat_id': chat_obj['id'],
        'user_id': user_obj['id'],
        'permissions_obj': json.dumps({
            'can_send_messages': False,
            'can_send_media_messages': False,
            'can_send_polls': False,
            'can_send_other_messages': False,
            'can_add_web_page_previews': False,
            'can_change_info': False,
            'can_pin_messages': False,
        }),
        'until_date': until_date,
    }
    API.restrictChatMember(**data)


def webhook(request):
    if request.method == 'POST':
        t_data = json.loads(request.body)
        pprint(t_data)
        # return JsonResponse({
        #     'ok': True,
        # })

        message_obj = t_data.get('message', {}) or t_data.get('edited_message', {})
        reply_obj = message_obj.get('reply_to_message')

        old_group_id = message_obj.get('migrate_from_chat_id', None)
        if old_group_id:
            old_group = Groups.objects.get(id=old_group_id)
            new_group = Groups.objects.create(
                id=message_obj['chat']['id'],
                title=message_obj['chat']['title']
            )
            Info.objects.filter(
                chat=old_group,
            ).update(chat=new_group)
            old_group.delete()

            return JsonResponse({
                'ok': 'POST request processed'
            })


        return JsonResponse({
            'ok': 'POST request processed'
        })
