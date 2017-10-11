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


class CommandHandler(Logger):
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
        methods = map(lambda m: m[1], inspect.getmembers(plugin,
                                                         inspect.ismethod))

        is_command = lambda m: hasattr(m, 'is_command')
        commands = [method for method in methods if is_command(method)]

        return commands

    def load_commands(self):
        self.commands = self.get_commands()

    def on_message_create(self, guild, message):
        for command in self.commands:
            gevent.spawn(self.handle_command, command, guild, message)

    def handle_command(self, command, guild, message):
        # check if command in called
        if not message.content.startswith('!' + command.name):
            return

        # build the context of the command call
        ctx = Context(message=message,
                      guild=guild)

        # if command is optional, check if it's activated
        if hasattr(command, 'optional'):
            check =  ctx.guild.storage.get(command.name)
            if not check:
                return

        # initialize an interaction for stats purpose
        interaction = Interaction(command, ctx)

        regex = command.regex
        match = regex.match(message.content)
        if not match:
            # if doesn't match, the command is malformed
            response = Response(code=400)
        else:
            # actually call the command and get the response
            args = match.groupdict()
            response = command(ctx, **args)

        if response:
            interaction.response = response
            try:
                response.send(self.bot, ctx.message.channel)
            finally:
                interaction.save()
