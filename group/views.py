import json

from django.http import JsonResponse
from pprint import pprint

from group.models import Blacklist, Gratitudes, Groups, Info, Members, Swearing, Whitelist

from time import mktime

from django.utils import timezone
from group.telegram_bot_api import API

import re
from group import urlmarker
import functools


def custom_search(iterable, obj):
    result = list()
    for element in iterable:
        if element in obj:
            result.append(obj)
    return result


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
        chat=Groups.objects.get_or_create(id=chat_obj['id'], title=chat_obj['title'])[0],
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
            chat=Groups.objects.get_or_create(
                id=chat_obj['id'],
                title=chat_obj['title'],
            )[0],
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

        if message_obj['chat'].get('type') == 'private':
            return JsonResponse({
                'ok': 'POST request processed'
            })

        old_group_id = message_obj.get('migrate_from_chat_id', None)
        if old_group_id:
            old_group, _ = Groups.objects.get_or_create(id=old_group_id, title=message_obj['chat']['title'])
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

        new_chat_members = message_obj.get('new_chat_members')
        if new_chat_members:
            for new_chat_member in new_chat_members:
                if new_chat_member['id'] != API.BOT_ID:
                    user, _ = Members.objects.get_or_create(
                        id=new_chat_member['id'],
                        username=new_chat_member['first_name'],
                    )
                    Info.objects.create(
                        user=user,
                        chat=Groups.objects.get_or_create(
                            id=message_obj['chat']['id'],
                            title=message_obj['chat']['title'],
                        )[0],
                    )
                else:
                    Groups.objects.create(
                        id=message_obj['chat']['id'],
                        title=message_obj['chat']['title']
                    )
                API.deleteMessage(message_obj['chat']['id'], message_obj['message_id'])
                return JsonResponse({
                    'ok': 'POST request processed'
                })

        left_chat_member = message_obj.get('left_chat_member')
        if left_chat_member:
            if left_chat_member['id'] != API.BOT_ID:
                user, _ = Members.objects.get_or_create(
                    id=left_chat_member['id'],
                    username=left_chat_member['first_name'],
                )
                Info.objects.filter(
                    user=user,
                    chat=Groups.objects.get_or_create(id=message_obj['chat']['id'], title=message_obj['chat']['id'])[0],
                ).delete()
                API.deleteMessage(message_obj['chat']['id'], message_obj['message_id'])
            else:
                Info.objects.filter(
                    chat=Groups.objects.get_or_create(id=message_obj['chat']['id'], title=message_obj['chat']['title'])[0],
                ).delete()
                Groups.objects.filter(id=message_obj['chat']['id']).delete()
            return JsonResponse({
                'ok': 'POST request processed'
            })

        if message_obj:
            group, _ = Groups.objects.get_or_create(id=message_obj['chat']['id'], title=message_obj['chat']['title'])
            group.messages_in_last_interval += 1
            group.save()

        if message_obj.get('text') == '!ro' and reply_obj:
            admins = API.getChatAdministrators(message_obj['chat']['id']).get('result', [])
            is_muted_by_admin = message_obj['from']['id'] in [admin_data['user']['id'] for admin_data in admins]
            if is_muted_by_admin:
                mute_user(message_obj['chat'], reply_obj['from'])
            API.deleteMessage(reply_obj['chat']['id'], reply_obj['message_id'])

        return JsonResponse({
            'ok': 'POST request processed'
        })
