from discord.types import Embed
from math import ceil
from time import time
from disco.api.http import APIException

"""
    Error codes:
    ------------
    200 -> OK
    500 -> INTERNAL_ERROR
    404 -> NOT_FOUND
    400 -> MALFORMED
    403 -> FORBIDDEN
"""
DEFAULT_MESSAGES = {200: 'Consider it done 👌',
                    500: 'An error occured in Mee6 land 🤕',
                    404: 'I didn\'t find anything 😭 .',
                    400: 'You\'re doing it wrong mate 😅 .',
                    403: 'Sorry, you are not authorized to use that command 🙄 .'}


class Response(object):
    def __init__(self, message='', embed=None, code=200):
        self._message = message
        self.embed = embed
        self.code = code
        if type(embed) == dict:
            self.embed = Embed(embed)

        self.sent_at = None

    @property
    def sent(self):
        return self.sent_at is not None

    @property
    def message(self):
        if self._message is not None:
            return self._message
        return DEFAULT_MESSAGES[self.code]

    @property
    def fail_safe_message(self):
        if not self.embed:
            return ""
        return self.embed.fail_safe_message

    def send_message(self, bot, destination, message="", embed=None):
        r = bot.send_message(destination, message, embed)
        self.sent_at = ceil(time())
        return r

    def send(self, bot, destination):
        try:
            r = self.send_message(bot, destination, self.message, self.embed)
        except APIException as e:
            if e.code in (50004, 50013) and self.embed:
                r = self.send_message(bot, destination, self.embed.fail_safe_message)
            else:
                raise e
