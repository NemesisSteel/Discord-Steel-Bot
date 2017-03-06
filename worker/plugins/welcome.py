from plugin import Plugin
from utils import fmt

import gevent

class Welcome(Plugin):
    def on_member_join(self, guild, member):
        welcome_message = fmt(guild.storage.get('welcome_message'),
                              server=guild.name,
                              user=member.mention)

        announcement_channel = guild.storage.get('channel_name')
        private = guild.storage.get('private')

        destination = announcement_channel or guild.id
        if private:
            destination = member.id

        self.send_message(destination, welcome_message)

    def on_member_remove(self, guild, member):
        gb_message = guild.storage.get('gb_message')
        if guild.storage.get('gb_disabled') or not gb_message:
            return

        gb_message = fmt(gb_message,
                         server=guild.name,
                         user=member.name)

        channel = guild.storage.get('channel_name')
        destination = channel or guild.id

        self.send_message(destination, gb_message)
