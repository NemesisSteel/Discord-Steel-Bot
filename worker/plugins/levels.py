from random import randint
from plugins.base import Base
from collections import defaultdict
from utils import fmt
from copy import copy

XP_REWARD_RANGE = (15, 25)
COOLDOWN_DURATION = 60

lvls_xp = [5*(i**2)+50*i+100 for i in range(200)]

def get_level_from_xp(xp):
    remaining_xp = int(xp)
    lvl = 0
    while remaining_xp >= lvls_xp[lvl]:
        remaining_xp -= lvls_xp[lvl]
        lvl += 1
    return lvl


class Player():
    def __init__(self, guild, member):
        self._guild = guild
        self.guild_id = guild.id
        self.member_id = member.id

        self._storage = guild.storage

    @property
    def lvl(self):
        return get_level_from_xp(self.xp)

    @property
    def xp(self):
        return int(self._storage.get('player:{}:xp'.format(self.member_id)) or 0)

    @xp.setter
    def xp(self, xp):
        return self._storage.set('player:{}:xp'.format(self.member_id), xp)


class Levels(Base):

    players = defaultdict(dict)

    def get_player(self, g, member):
        cached_player = self.players[g.id].get(member.id)
        if cached_player:
            return cached_player

        player = Player(g,
                        member)
        self.players[g.id][member.id] = player

        return player

    def is_member_banned(self, guild, member):
        banned_roles = guild.storage.smembers('banned_roles')
        for role in member.roles:
            if str(role.id) in banned_roles:
                return True
        return False

    def on_message_create(self, guild, message):
        storage = guild.storage

        # check if member is banned from gaining lvls
        if self.is_member_banned(guild, message.author):
            return

        # check member's CD
        cooldown_key = 'player:{}:check'.format(message.author.id)
        print(cooldown_key)
        print(storage.get(cooldown_key))
        if storage.get(cooldown_key) and False:
            return
        # activating CD
        storage.set(cooldown_key, '1', ex=COOLDOWN_DURATION)

        # get the player
        player = self.get_player(guild, message.author)
        player_lvl = copy(player.lvl)

        new_xp = randint(*XP_REWARD_RANGE)
        print('adding xp to {}'.format(message.author.id))
        print(player.xp)
        player.xp += new_xp
        print(player.xp)

        # adding the player (in case of not added)
        storage.sadd('players', message.author.id)

        has_lvl_up = player.lvl != player_lvl
        print('lvl')
        print(player.lvl)
        print(player_lvl)
        if has_lvl_up:
            announcement_enabled = storage.get('announcement_enabled')
            if not announcement_enabled:
                return

            should_whisp = storage.get('whisp')

            if should_whisp:
                destination = message.author
            else:
                destination = message.channel

            announcement_fmt = storage.get('announcement')
            announcement = fmt(announcement_fmt,
                               player=message.author.mention,
                               level=player.lvl)
            self.send_message(destination, announcement)
