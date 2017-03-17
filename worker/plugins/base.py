import gevent
import inspect

from collections import defaultdict
from logger import Logger
from constants import EVENTS
from cmd import Command


class Base(Logger):

    def __init__(self, bot):
        self.bot = bot
        self.listeners = defaultdict(list)
        self.register_default_listeners()
        self.command = Command(self)
        self.name = self.__class__.__name__

        self.send_message = bot.send_message

    def __str__(self):
        return 'plugin.{}'.format(self.name.lower())

    def register_default_listeners(self):
        for event in EVENTS:
            try:
                default_listener = getattr(self, 'on_' + event.lower())
            except AttributeError as e:
                continue
            self.register_listener(event, default_listener)

    def register_listener(self, event_name, listener):
        self.listeners[event_name].append(listener)

    def dispatch(self, event_name="", *args, **kwargs):
        for listener in self.listeners[event_name]:
            gevent.spawn(listener, *args, **kwargs)
