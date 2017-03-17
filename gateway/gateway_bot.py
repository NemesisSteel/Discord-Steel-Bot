import discord
import aioredis
import inspect
import asyncio
import os
import re
import json
import math

from utils import dump, find, parse_redis_url
from logger import Logger
from time import time
from aiohttp import web
from rpc import RPCServer, rpc, RPCException
from collections import defaultdict

if not discord.opus.is_loaded():
    if platform == 'linux' or platform == 'linux2':
        discord.opus.load_opus('./libopus.so')
    elif platform == 'darwin':
        discord.opus.load_opus('libopus.dylib')

class GatewayBot(discord.Client, Logger):

    players = dict()
    call_next = defaultdict(lambda: True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fetch_offline_members = True

        self.broker_url = kwargs.get('broker_url')
        self.redis_url = kwargs.get('redis_url')

        self._redis_connect()
        self._broker_connect()

        self.rpc_server = RPCServer(self)

    def __str__(self):
        return 'gateway-{}-{}'.format(self.shard_id,
                                      self.shard_count)

    def _redis_connect(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.__redis_connect())

    def _broker_connect(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.__broker_connect())

    async def __redis_connect(self):
        self.redis = await aioredis.create_redis(
            parse_redis_url(self.redis_url),
            encoding='utf8'
        )

    async def __broker_connect(self):
        self.broker = await aioredis.create_redis(
            parse_redis_url(self.broker_url),
            encoding='utf8'
        )

    async def send(self, queue, data):
        payload = json.dumps(data)
        await self.broker.lpush(queue, payload)

    async def send_dispatch_event(self, event_type, guild, before=None,
                                  after=None):
        e = dict(ts=time(),
                 type=event_type,
                 producer=str(self),
                 guild=dump(guild))

        if before:
            if after:
                e['before'] = dump(before)
                e['after'] = dump(after)
            else:
                e['data'] = dump(before)

        self.log("{event}:{gid} @ {ts}".format(event=e['type'],
                                               gid=e['guild']['id'],
                                               ts=e['ts']))

        await self.send('discord.events.{}'.format(e['type']), e)

    # Events handling
    async def on_message(self, message):
        # Ignore private messages
        if not message.guild:
            return
        # Ignore WHs 
        if message.author.__class__ is not discord.Member:
            return

        await self.send_dispatch_event('MESSAGE_CREATE',
                                       message.guild,
                                       message)

    async def on_message_delete(self, message):
        # Ignore private messages
        if not message.guild:
            return
        # Ignore webhooks 
        if message.author.__class__ is not discord.Member:
            return

        await self.send_dispatch_event('MESSAGE_DELETE',
                                       message.guild,
                                       message)

    async def on_message_edit(self, before, after):
        # Ignore private messages
        if not after.guild:
            return
        # Ignore webhooks 
        if after.author.__class__ is not discord.Member:
            return

        await self.send_dispatch_event('MESSAGE_EDIT',
                                       after.guild,
                                       before,
                                       after)

    async def on_ready(self):
        self.log('Connected to {} guilds'.format(len(self.guilds)))
        self.rpc_server.run()
        for guild in list(self.guilds):
            self.loop.create_task(self.on_guild_ready(guild))

    async def on_guild_ready(self, guild):
        await self.send_dispatch_event('GUILD_READY',
                                       guild)

    async def on_guild_join(self, guild):
        await self.send_dispatch_event('GUILD_JOIN',
                                       guild)

    async def on_guild_remove(self, guild):
        await self.send_dispatch_event('GUILD_REMOVE',
                                       guild)

    async def on_guild_update(self, before, after):
        await self.send_dispatch_event('GUILD_UPDATE',
                                       after,
                                       before,
                                       after)

    async def on_member_join(self, member):
        await self.send_dispatch_event('MEMBER_JOIN',
                                       member.guild,
                                       member)

    async def on_member_remove(self, member):
        await self.send_dispatch_event('MEMBER_REMOVE',
                                       member.guild,
                                       member)

    # RPCs
    @rpc
    def get_guild(self, guild_id):
        guild = discord.utils.get(self.guilds, id=guild_id)
        if not guild:
            raise RPCException('guild_not_found')

        return guild

    @rpc
    def get_voice_channel(self, guild, voice_channel_id):
        if type(guild) in (str, int):
            guild = self.get_guild(guild)

        voice_channel = discord.utils.get(guild.channels, id=str(voice_channel_id))
        if not voice_channel:
            raise RPCException('voice_channel_not_found')

        if voice_channel.type != discord.ChannelType.voice:
            raise RPCException('not_a_voice_channel')

        return voice_channel

    @rpc
    async def join_voice(self, guild, voice_channel_id):
        if type(guild) in (str, int):
            guild = self.get_guild(guild)

        voice_channel = self.get_voice_channel(guild, voice_channel_id)

        voice = guild.voice_client
        if voice:
            await voice.move_to(voice_channel)
        else:
            await self.join_voice_channel(voice_channel)

        return voice_channel

    @rpc
    async def leave(self, guild):
        if type(guild) in (str, int):
            guild = self.get_guild(guild)

        voice = guild.voice_client
        if voice:
            await voice.disconnect()

        return None

    @rpc
    def get_voice_client(self, guild):
        if type(guild) in (str, int):
            guild = self.get_guild(guild)

        voice = guild.voice_client
        if not voice:
            raise RPCException('voice_not_connected')

        return voice

    async def _ytdl_play_song(self, guild, song_url, after=None):
        if type(guild) in (str, int):
            guild = self.get_guild(guild)

        voice = self.get_voice_client(guild)

        lock = self.play_locs[guild.id]
        try:
            await lock.acquire()

            curr_player = self.players.get(guild.id)
            if curr_player:
                self.call_next[guild.id] = False
                curr_player.stop()

            player = await voice.create_ytdl_player(url,
                                                    ytdl_options=opts,
                                                    after=after)
            self.players[guild.id] = player
            player.volume = 0.6
            player.start()
        finally:
            lock.release()
            return voice

    @rpc
    async def ytdl_play_song(self, guild, song_url):
        return self._ytdl_play_song(guild, song_url)

    @rpc
    async def ytdl_play_songs(self, guild, queue_name):
        def n(player):
            if player.error:
                e = player.error
                import traceback
                log('Error from the player')
                log(traceback.format_exception(type(e), e, None))
            if self.call_next.get(guild.id):
                self.loop.create_task(self.ytdl_play_songs(guild, queue_name))
            self.call_next[guild.id] = True

        song_url = redis.rpop(queue_name)
        if song_url:
            return await self._ytdl_play_song(guild, song_url, after=n)

        return None
