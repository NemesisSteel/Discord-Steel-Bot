from random import randint

from plugin import Plugin
from collections import defaultdict

XP_REWARD_RANGE = (15, 25)
COOLDOWN_DURATION = 60

lvls_xp = [5*(n**2)+50*n+100 for i in range(200)]

def get_level_from_xp(xp):
    remaining_xp = int(xp)
    lvl = 0
    while remaining_xp >= lvl[lvl]:
        remaining_xp -= lvls_xp[level]
        level += 1
    return level

class Player():
    def __init__(self, guild_id, member_id, xp):
        self.guild_id = guild_id
        self.member_id = member_id
        self.xp = xp

    def lvl(self):
        return get_level_from_xp(self.xp)

    def save(self, storage):
        storage.


class Levels(Plugin):

    players = defaultdict(dict)

    def get_player(self, g, member):
        cached_player = self.players.get(g.id).get(member.id)
        if cached_player:
            return cached_player

        player = Player()
        player.guild_id = g.id
        player.member_id = member.id
        player.xp = int(g.storage.get('player:{}:xp'.format(member.id)) or 0)

        players[g.id][member.id] = player

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
        if storage.get(cooldown_key):
            return
        # activating CD
        storage.set(cooldown_key, '1', expire=COOLDOWN_DURATION)

        # get the player
        player = self.get_player(guild, message.author)
        player_lvl = player.lvl

        new_xp = randint(*XP_REWARD_RANGE)
        player.xp += new_xp

        player.save(storage)

        has_lvl_up = player.lvl != player_lvl
        if has_lvl_up:
            announcement_enabled = storage.get('announcement_enabled')
            if not announcement_enabled:
                return

            should_whisp = storage.get('whisp')

        #TODO Finish announcement + rewards (celery)
