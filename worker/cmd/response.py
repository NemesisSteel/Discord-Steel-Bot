from discord.types import Embed
from math import ceil
from time import time


class Response(object):
    def __init__(self, message='', embed=None):
        self.message = message
        self.embed = embed
        if type(embed) == dict:
            self.embed = Embed(embed)

        self.sent_at = None

    @property
    def sent(self):
        return self.sent_at is not None

    @property
    def fail_safe_message(self):
        if not self.embed:
            return ""
        return self.embed.fail_safe_message

    def send(self, bot, destination):
        bot.send_message(destination, self.message, self.embed)
        self.sent_at = ceil(time())
