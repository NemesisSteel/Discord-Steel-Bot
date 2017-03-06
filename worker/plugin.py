from collections import defaultdict

from constants import EVENTS

import gevent
import cmd
import logging
import inspect

logging.basicConfig(level=logging.INFO)

class Plugin:

    __global__ = False
    listeners = defaultdict(list)

    def __init__(self, bot):
        self.bot = bot
        self.register_default_listeners()
        self.register_listener('MESSAGE_CREATE', self.command_handler)
        self.log = logging.getLogger('plugin.' + self.__class__.__name__.lower()).info

    def get_commands(self):
        methods = inspect.getmembers(self, inspect.ismethod)
        is_command = lambda m: hasattr(m, 'is_command')
        commands = list(filter(is_command, methods))
        commands = list(map(lambda m: m[1], commands))
        return commands

    def command_handler(self, guild, message):
        for command in self.get_commands():
            gevent.spawn(cmd.command_handler, command)

    def register_default_listeners(self):
        for event in EVENTS:
            try:
                default_listener = getattr(self, 'on_' + event.lower())
            except AttributeError as e:
                continue
            self.register_listener(event, default_listener)

    def register_listener(self, event_name, listener):
        self.listeners[event_name].append(listener)

    def send_message(self, destination, message, embed=None):
        return self.bot.api.channels_messages_create(int(destination),
                                                     message,
                                                     embed=embed)

    def dispatch(self, event_name="", *args, **kwargs):
        for listener in self.listeners.get(event_name, []):
            gevent.spawn(listener, *args, **kwargs)
