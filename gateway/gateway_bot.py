import discord
import aioredis
import inspect
import asyncio
import os
import re
import json
import math
import logging

from utils import dump
from time import time
from aiohttp import web

if not discord.opus.is_loaded():
    if platform == 'linux' or platform == 'linux2':
        discord.opus.load_opus('./libopus.so')
    elif platform == 'darwin':
        discord.opus.load_opus('libopus.dylib')

logging.basicConfig(level=logging.INFO)

def parse_redis_url(redis_url):
	pattern = r'redis:\/\/([a-zA-Z0-9.]*):?([0-9]*)?'
	result = re.match(pattern, redis_url).groups()

	if result[1]:
		return (result[0], int(result[1]))

	return (result[0], 6379)

class RPCException(Exception):
    pass

def make_handler(func):
    async def handler(request):
        args_list = [request.match_info[arg] for arg in \
                     func.rpc_info['args']]
        try:
            if inspect.iscoroutinefunction(func):
                resp = await func(*args_list)
            else:
                resp = func(*args_list)
        except RPCException as e:
            return web.json_response({'error': str(e)}, status=500)
        print(resp)
        return web.json_response({'msg': 'ok'})
    return handler

def rpc(method):
    args = list(inspect.signature(method).parameters)[1:]
    method_name = method.__name__

    method.is_rpc = True
    print(args)
    method.rpc_info = {'name': method_name,
                       'args': args}
    return method

class GatewayBot(discord.Client):

    players = dict()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.broker_url = kwargs.get('broker_url')
        self.redis_url = kwargs.get('redis_url')

        self.redis_connect()
        self.broker_connect()

        self.gateway_repr = 'gateway-{}-{}'.format(self.shard_id,
                                                   self.shard_count)
        self.log = logging.getLogger(self.gateway_repr).info

        self.rpc_app = web.Application()
        self.rpc_app.router.add_get('/', self.rpc_hello)
        self.register_rpcs()

    def register_rpcs(self):
        attrs = map(lambda attr_name: getattr(self, attr_name), dir(self))
        methods = filter(inspect.ismethod, attrs)
        rpcs = filter(lambda m: hasattr(m, 'is_rpc'), methods)
        for rpc in rpcs:
            info = rpc.rpc_info
            path = '/{}'.format(info['name'])
            if len(info['args']):
                path += '/'
            path += '/'.join(map(lambda a: '{' + a + '}', info['args']))
            print(path)
            self.rpc_app.router.add_get(path, make_handler(rpc))

    def run_rpc_server(self):
        handler = self.rpc_app.make_handler()
        srv = self.loop.create_server(handler, '0.0.0.0', 8080)
        self.loop.create_task(srv)
        self.log('RPC serving on 0.0.0.0:8080')

    def rpc_hello(self, request):
        rsp = {'id': self.gateway_repr,
               'guilds_count': len(self.servers)}
        self.log(request.match_info)
        return web.json_response(rsp)

    def redis_connect(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._redis_connect())

    def broker_connect(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._broker_connect())

    async def _redis_connect(self):
        self.redis = await aioredis.create_redis(
            parse_redis_url(self.redis_url),
            encoding='utf8'
        )

    async def _broker_connect(self):
        self.broker = await aioredis.create_redis(
            parse_redis_url(self.broker_url),
            encoding='utf8'
        )

    async def send(self, queue, data):
        payload = json.dumps(data)
        await self.broker.lpush(queue, payload)

    async def ping(self):
        PING_INTERVAL = 10

        while True:
            data = {
                'ts': time(),
                'guild_count': len(self.servers),
            }
            payload = json.dumps(data)

            await self.redis.setex(self.gateway_repr,
                                   math.floor(PING_INTERVAL * 1.5),
                                   payload)
            await asyncio.sleep(PING_INTERVAL)

    async def send_dispatch_event(self, event_type, server, before=None,
                                  after=None):
        e = dict(ts=time(),
                 type=event_type,
                 producer=self.gateway_repr,
                 guild=dump(server))

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

    async def on_message(self, message):
        # Ignore private messages
        if not message.server:
            return
        # Ignore WHs 
        if message.author.__class__ is not discord.Member:
            return

        await self.send_dispatch_event('MESSAGE_CREATE',
                                       message.server,
                                       message)

    async def on_message_delete(self, message):
        # Ignore private messages
        if not message.server:
            return
        # Ignore WHs 
        if message.author.__class__ is not discord.Member:
            return

        await self.send_dispatch_event('MESSAGE_DELETE',
                                       message.server,
                                       message)

    async def on_message_edit(self, before, after):
        # Ignore private messages
        if not after.server:
            return
        # Ignore WHs 
        if after.author.__class__ is not discord.Member:
            return

        await self.send_dispatch_event('MESSAGE_EDIT',
                                       after.server,
                                       before,
                                       after)

    async def on_ready(self):
        self.log('Connected to {} guilds'.format(len(self.servers)))
        self.run_rpc_server()
        self.loop.create_task(self.ping())
        for server in list(self.servers):
            self.loop.create_task(self.on_server_ready(server))

    async def on_server_ready(self, server):
        await self.send_dispatch_event('GUILD_READY',
                                       server)

    async def on_server_join(self, server):
        await self.send_dispatch_event('GUILD_JOIN',
                                       server)

    async def on_server_remove(self, server):
        await self.send_dispatch_event('GUILD_REMOVE',
                                       server)

    async def on_server_update(self, before, after):
        await self.send_dispatch_event('GUILD_UPDATE',
                                       after,
                                       before,
                                       after)

    async def on_member_join(self, member):
        await self.send_dispatch_event('MEMBER_JOIN',
                                       member.server,
                                       member)

    async def on_member_remove(self, member):
        await self.send_dispatch_event('MEMBER_REMOVE',
                                       member.server,
                                       member)

    @rpc
    def get_server(self, server_id):
        server = discord.utils.get(self.servers, id=server_id)
        if not server:
            raise RPCException('Guild not found')

        return server

    @rpc
    def get_voice_channel(self, server, voice_channel_id):
        print(server, voice_channel_id)
        if type(server) in (str, int):
            server = self.get_server(server)

        voice_channel = discord.utils.get(server.channels, id=str(voice_channel_id))
        if not voice_channel:
            raise RPCException('Voice channel not found')

        if voice_channel.type != discord.ChannelType.voice:
            raise RPCException('This is not a voice channel')

        return voice_channel

    @rpc
    async def join_voice(self, server, voice_channel_id):
        if type(server) in (str, int):
            server = self.get_server(server)

        voice_channel = self.get_voice_channel(server, voice_channel_id)

        voice = server.voice_client
        if voice:
            await voice.move_to(voice_channel)
        else:
            await self.join_voice_channel(voice_channel)

        return voice_channel

    @rpc
    async def leave(self, server):
        if type(server) in (str, int):
            server = self.get_server(server)

        voice = server.voice_client
        if voice:
            await voice.disconnect()

        return None

    @rpc
    def get_voice_client(self, server):
        if type(server) in (str, int):
            print(server)
            print(type(server))
            server = self.get_server(server)

        voice = server.voice_client
        print(voice)
        if not voice:
            raise RPCException('Not connected to voice')

        return voice

    @rpc
    async def ytdl_play_song(self, server, song_url):
        if type(server) in (str, int):
            print(server)
            print(type(server))
            server = self.get_server(server)
            print(server)

        voice = self.get_voice_client(server)

        lock = self.play_locs[guild.id]
        await lock.acquire()

        curr_player = self.players.get(server.id)
        if curr_player:
            self.call_next[server.id] = False
            curr_player.stop()

        player = await voice.create_ytdl_player(url,
                                                ytdl_options=opts)

        self.players[guild.id] = player
        player.volume = 0.6
        player.start()

        lock.release()

        return voice
