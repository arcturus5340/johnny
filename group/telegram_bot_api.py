import json
import requests


class API:
    TOKEN = '1367204126:AAFmR048ECJfBht5pOJA2Xn94WsJkJe6ydg'
    BOT_ID = 1367204126


    @classmethod
    def answerCallbackQuery(cls, callback_query_id, text):
        response = requests.post(f'https://api.telegram.org/bot{cls.TOKEN}/answerCallbackQuery', data={
            'callback_query_id': callback_query_id,
            'text': text,
        })
        return json.loads(response.content)

    @classmethod
    def deleteMessage(cls, chat_id, message_id):
        response = requests.post(f'https://api.telegram.org/bot{cls.TOKEN}/deleteMessage', data={
            'chat_id': chat_id,
            'message_id': message_id,
        })
        return json.loads(response.content)

    @classmethod
    def getChatAdministrators(cls, chat_id):
        response = requests.post(f'https://api.telegram.org/bot{cls.TOKEN}/getChatAdministrators', data={
            'chat_id': chat_id,
        })
        return json.loads(response.content)

    @classmethod
    def kickChatMember(cls, chat_id, user_id):
        response = requests.post(f'https://api.telegram.org/bot{cls.TOKEN}/kickChatMember', data={
            'chat_id': chat_id,
            'user_id': user_id,
        })
        return json.loads(response.content)

    @classmethod
    def getChatMember(cls, chat_id, user_id):
        response = requests.post(f'https://api.telegram.org/bot{cls.TOKEN}/getChatMember', data={
            'chat_id': chat_id,
            'user_id': user_id,
        })
        return json.loads(response.content)

    @classmethod
    def restrictChatMember(cls, chat_id, user_id, permissions_obj, until_date):
        response = requests.post(f'https://api.telegram.org/bot{cls.TOKEN}/restrictChatMember', data={
            'chat_id': chat_id,
            'user_id': user_id,
            'permissions': permissions_obj,
            'until_date': until_date
        })
        return json.loads(response.content)

    @classmethod
    def sendMessage(cls, chat_id, text, parse_mode, reply_markup=None):
        response = requests.post(f'https://api.telegram.org/bot{cls.TOKEN}/sendMessage', data={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'reply_markup': reply_markup,
        })
        return json.loads(response.content)
