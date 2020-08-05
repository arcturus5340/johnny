import json

from django.http import JsonResponse
from pprint import pprint

from group.models import Blacklist, Gratitudes, GlobalSettings, Groups, Info, Members, Swearing, Whitelist

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
    user, created = Members.objects.get_or_create(
        id=user_obj['id'],
        defaults={
            'username': user_obj['first_name'],
        }
    )
    group, _ = Groups.objects.get_or_create(id=chat_obj['id'], defaults={'title': chat_obj['title']})
    info, _ = Info.objects.get_or_create(
        user=user,
        chat=group,
        defaults={
            'date_joined': timezone.now() - timezone.timedelta(days=2),
        }
    )
    info.mute_rating += 1
    info.save()
    if info.mute_rating == 1:
        until_date = int(mktime((timezone.now() + timezone.timedelta(hours=6)).timetuple()))
        text = '{} перемещен в карантин на <b>6 часов</b> за <b>первое нарушение</b>.'.format(user_obj['first_name'])
        API.sendMessage(chat_obj['id'], text, 'html')
    elif info.mute_rating == 2:
        until_date = int(mktime((timezone.now() + timezone.timedelta(hours=12)).timetuple()))
        text = '{} перемещен в карантин на <b>12 часов</b> за <b>второе нарушение</b>.'.format(user_obj['first_name'])
        API.sendMessage(chat_obj['id'], text, 'html')
    elif info.mute_rating == 3:
        until_date = int(mktime((timezone.now() + timezone.timedelta(hours=24)).timetuple()))
        text = '{} перемещен в карантин на <b>24 часа</b> за <b>третье нарушение</b>.'.format(user_obj['first_name'])
        print(API.sendMessage(chat_obj['id'], text, 'html'))
    else:
        text = '{} удален из чата за <b>четвертое нарушение</b>.'.format(user_obj['first_name'])
        API.sendMessage(chat_obj['id'], text, 'html')
        API.kickChatMember(
            chat_obj['id'],
            user_obj['id']
        )
        Info.objects.filter(
            user=user,
            chat=Groups.objects.get_or_create(
                id=chat_obj['id'],
                defaults={
                    'title': chat_obj['title'],
                }
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

        message_obj = t_data.get('message', {}) or t_data.get('edited_message', {})
        reply_obj = message_obj.get('reply_to_message')

        if message_obj['chat'].get('type') == 'private':
            activation_key_match = re.search(r'^/activate\s(\S+).*$', message_obj.get('text', ''))
            if activation_key_match:
                activation_key = activation_key_match.group(1)
                if activation_key == GlobalSettings.objects.get(setting='ActivationKey').value:
                    Members.objects.update_or_create(
                        id=message_obj['from']['id'],
                        defaults={
                            'username': message_obj['from']['first_name'],
                            'private_chat_id': message_obj['chat']['id'],
                            'is_admin': True,
                        }
                    )
                    text = 'Вы указали верный ключ и отныне входите в число администраторов бота'
                    API.sendMessage(message_obj['chat']['id'], text, 'html')

        if message_obj['chat'].get('type') != 'supergroup':
            return JsonResponse({
                'ok': 'POST request processed'
            })

        old_group_id = message_obj.get('migrate_from_chat_id', None)
        if old_group_id:
            old_group, _ = Groups.objects.get_or_create(id=old_group_id, defaults={'title': message_obj['chat']['title']})
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
                        defaults={
                            'username': new_chat_member['first_name'],
                        }
                    )
                    Info.objects.get_or_create(
                        user=user,
                        chat=Groups.objects.get_or_create(
                            id=message_obj['chat']['id'],
                            defaults={
                                'title': message_obj['chat']['title'],
                            }
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
                    defaults={'username': left_chat_member['first_name']},
                )
                Info.objects.filter(
                    user=user,
                    chat=Groups.objects.get_or_create(id=message_obj['chat']['id'], defaults={'title': message_obj['chat']['id']})[0],
                ).delete()
                API.deleteMessage(message_obj['chat']['id'], message_obj['message_id'])
            else:
                Info.objects.filter(
                    chat=Groups.objects.get_or_create(id=message_obj['chat']['id'], defaults={'title': message_obj['chat']['title']})[0],
                ).delete()
                Groups.objects.filter(id=message_obj['chat']['id']).delete()
            return JsonResponse({
                'ok': 'POST request processed'
            })

        if message_obj:
            group, _ = Groups.objects.get_or_create(id=message_obj['chat']['id'], defaults={'title': message_obj['chat']['title']})

            group.messages_in_last_interval += 1
            group.save()

        if message_obj.get('text') == '!ro' and reply_obj:
            admins = API.getChatAdministrators(message_obj['chat']['id']).get('result', [])
            is_muted_by_admin = message_obj['from']['id'] in [admin_data['user']['id'] for admin_data in admins]
            if is_muted_by_admin:
                mute_user(message_obj['chat'], reply_obj['from'])
                API.deleteMessage(reply_obj['chat']['id'], reply_obj['message_id'])

        text_words = set(re.split('[\n .,?!:()]', message_obj.get('text', '').lower()))

        gratitude_words = set(Gratitudes.objects.values_list('word', flat=True))
        has_message_gratitude = False
        if reply_obj and (text_words & gratitude_words) and (reply_obj['from']['id'] != API.BOT_ID) and not reply_obj['from']['is_bot']:
            if reply_obj['from']['id'] == message_obj['from']['id']:
                return JsonResponse({
                    'ok': 'POST request processed'
                })

            user, created = Members.objects.get_or_create(
                id=reply_obj['from']['id'],
                defaults={'username': reply_obj['from']['first_name']},
            )
            info, _ = Info.objects.get_or_create(
                user=user,
                chat=Groups.objects.get_or_create(id=message_obj['chat']['id'], defaults={'title': message_obj['chat']['title']})[0],
                defaults={'date_joined': timezone.now() - timezone.timedelta(days=2)},
            )
            info.rating += 1
            info.save()
            text = 'Репутация <b>{}</b> увеличена на 1.\nВсего очков репутации: <b>{}</b>'.format(reply_obj['from']['first_name'], info.rating)
            API.sendMessage(message_obj['chat']['id'], text, 'html')
            has_message_gratitude = True

        swearing_words = set(Swearing.objects.values_list('word', flat=True))
        swearing_words_in_text = [custom_search(swearing_words, word) for word in text_words]
        swearing_words_in_text = {item for sublist in swearing_words_in_text for item in sublist}
        if swearing_words_in_text - set(Whitelist.objects.values_list('word', flat=True)):
            API.deleteMessage(message_obj['chat']['id'], message_obj['message_id'])

            if has_message_gratitude:
                mute_user(message_obj['chat'], message_obj['from'])

            return JsonResponse({
                'ok': 'POST request processed'
            })

        admins = API.getChatAdministrators(message_obj['chat']['id']).get('result', [])
        is_admin = message_obj['from']['id'] in (admin_data['user']['id'] for admin_data in admins)
        if not is_admin:
            document = t_data.get('message', {}).get('document', {})
            if document:
                API.deleteMessage(message_obj['chat']['id'], message_obj['message_id'])
                return JsonResponse({
                    'ok': 'POST request processed'
                })

            for mention in (word for word in text_words if word.startswith('@')):
                if custom_search(Blacklist.objects.values_list('link', flat=True), mention):
                    API.deleteMessage(message_obj['chat']['id'], message_obj['message_id'])
                    data = {
                        'chat_id': message_obj['chat']['id'],
                        'user_id': message_obj['from']['id'],
                        'permissions_obj': json.dumps({
                            'can_send_messages': False,
                            'can_send_media_messages': False,
                            'can_send_polls': False,
                            'can_send_other_messages': False,
                            'can_add_web_page_previews': False,
                            'can_change_info': False,
                            'can_pin_messages': False,
                        }),
                        'until_date': int(mktime((timezone.now() + timezone.timedelta(hours=24)).timetuple())),
                    }
                    API.restrictChatMember(**data)
                    text = '{} перемещен в карантин на <b>24 часа</b> за <b>размещение нежелательной ссылки</b>.'.format(
                        message_obj['from']['first_name'])
                    API.sendMessage(message_obj['chat']['id'], text, 'html')
                    return JsonResponse({
                        'ok': 'POST request processed'
                    })

            entities = message_obj.get('entities', [])
            entities.extend(message_obj.get('caption_entities', []))
            for entity in entities:
                if entity['type'] in ['url', 'mention', 'text_link']:
                    entity_content = message_obj.get('text', '') or message_obj.get('caption', '')
                    url = entity_content[entity['offset']:entity['offset']+entity['length']]
                    if custom_search(Blacklist.objects.values_list('link', flat=True), url):
                        API.deleteMessage(message_obj['chat']['id'], message_obj['message_id'])
                        data = {
                            'chat_id': message_obj['chat']['id'],
                            'user_id': message_obj['from']['id'],
                            'permissions_obj': json.dumps({
                                'can_send_messages': False,
                                'can_send_media_messages': False,
                                'can_send_polls': False,
                                'can_send_other_messages': False,
                                'can_add_web_page_previews': False,
                                'can_change_info': False,
                                'can_pin_messages': False,
                            }),
                            'until_date': int(mktime((timezone.now() + timezone.timedelta(hours=24)).timetuple())),
                        }
                        API.restrictChatMember(**data)
                        text = '{} перемещен в карантин на <b>24 часа</b> за <b>размещение нежелательной ссылки</b>.'.format(message_obj['from']['first_name'])
                        API.sendMessage(message_obj['chat']['id'], text, 'html')
                        return JsonResponse({
                            'ok': 'POST request processed'
                        })

        return JsonResponse({
            'ok': 'POST request processed'
        })
