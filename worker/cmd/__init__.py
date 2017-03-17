import re
import inspect
import gevent

from logger import Logger
from exceptions import BotException, NotFound
from cmd.interaction import Interaction
from cmd.context import Context
from cmd.response import Response
from time import time
from math import ceil

def _get_command_name(command):
    pattern = r'^!([a-zA-Z0-9_\-]*)'
    match = re.match(pattern, command)

    return match and match.group(1)

def _get_command_regex(command):
    pattern = '<(\w*):(\w*)>'
    args = re.findall(pattern, command)

    command_name = _get_command_name(command)

    regex = '^!{}'.format(command_name)

    arg_regex = {'member': '<@!?(?P<ARG_NAME>[0-9]*)>',
                 'channel': '<#(?P<ARG_NAME>[0-9]*)>',
                 'role': '<@&(?P<ARG_NAME>[0-9]*)>',
                 'str': '(?P<ARG_NAME>.*)',
                 'int': '(?P<ARG_NAME>[0-9]*)'}
    for arg_name, arg_type in args:
        arg_type_regex = arg_regex.get(arg_type).replace('ARG_NAME',
                                                         arg_name)
        regex += '[ ]*' + arg_type_regex

    return regex

def hint(hint_str):
    def decorator(f):
        f.hint_str = f
        return f
    return decorator

def require_roles(*roles):
    def decorator(f):
        f.roles = roles
        return f
    return decorator

def optional(f):
    f.optional = True
    return f

def register(command):
    def decorator(f):
        regex = _get_command_regex(command)
        command_name = _get_command_name(command)

        f.is_command = True
        f.regex = re.compile(regex)
        f.command_name = command_name
        return f
    return decorator


class Command(Logger):

    def __init__(self, plugin):
        self.plugin = plugin
        self.bot = plugin.bot
        self.commands = []
        self.plugin.register_listener('MESSAGE_CREATE',
                                      self.on_message_create)
        self.load_commands()

    def __str__(self):
        return '{}.command'.format(self.bot)

    def get_commands(self):
        plugin = self.plugin
        methods = inspect.getmembers(plugin, inspect.ismethod)
        is_command = lambda m: hasattr(m[1], 'is_command')
        commands = list(filter(is_command, methods))
        commands = list(map(lambda m: m[1], commands))
        return commands

    def load_commands(self):
        self.commands = self.get_commands()

    def on_message_create(self, guild, message):
        for command in self.commands:
            gevent.spawn(self.command_handler, command, guild, message)

    def command_handler(self, command_func, guild, message):
        regex = command_func.regex
        match = regex.match(message.content)
        if not match:
            return

        import traceback
        import sys

        args = match.groupdict()

        ctx = Context(message=message,
                      guild=guild)

        if hasattr(command_func, 'optional'):
            check =  ctx.guild.storage.get(command_func.command_name)
            if not check:
                return

        interaction = Interaction(command_func, ctx)

        try:
            response = command_func(ctx, **args)
        except BotException as e:
            response = Response(e.message)

        if response:
            interaction.response = response
            try:
                response.send(self.bot, ctx.message.channel)
            finally:
                interaction.save()
