import discord
import aioredis
import asyncio
import os
import re
import json
import math
import logging

from utils import dump
from time import time

logging.basicConfig(level=logging.INFO)

def parse_redis_url(redis_url):
	pattern = r'redis:\/\/([a-zA-Z0-9.]*):?([0-9]*)?'
	result = re.match(pattern, redis_url).groups()

	if result[1]:
		return (result[0], int(result[1]))

	return (result[0], 6379)

class GatewayBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.broker_url = kwargs.get('broker_url')
        self.redis_url = kwargs.get('redis_url')

        self.redis_connect()
        self.broker_connect()

        self.gateway_repr = 'gateway-{}-{}'.format(self.shard_id,
                                                   self.shard_count)
        self.log = logging.getLogger(self.gateway_repr).info

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

    async def on_ready(self):
        self.log('Connected to {} guilds'.format(len(self.servers)))
        self.loop.create_task(self.ping())

    async def ping(self):
        PING_INTERVAL = 10

        data = {
            'ts': time(),
            'guild_count': len(self.servers),
        }
        payload = json.dumps(data)

        await self.redis.setex(self.gateway_repr,
                               PING_INTERVAL,
                               payload)

    def event(self, event_type, server, before, after=None):
        """
            g: guild
            ts: event timestamp
            t: event type
            p: producer name (gateway-xx-xx)
            d: data
            b: before
            a: after
        """
        e = {'g': dump(server),
             'ts': time(),
             't': event_type,
             'p': self.gateway_repr}
        if after:
            e['b'] = dump(before)
            e['a'] = dump(after)
        else:
            e['d'] = dump(before)

        return e

    async def send_event(self, *args, **kwargs):
        e = self.event(*args, **kwargs)

        self.log("{event}:{gid} @ {ts}".format(event=e['t'],
                                                    gid=e['g']['id'],
                                                    ts=e['ts']))

        await self.send('discord.events.{}'.format(e['t']), e)

    async def on_message(self, message):
        # Ignore private messages
        if not message.server:
            return
        await self.send_event('MESSAGE_CREATE',
                              message.server,
                              message)

    async def on_message_delete(self, message):
        # Ignore private messages
        if not message.server:
            return
        await self.send_event('MESSAGE_DELETE',
                              message.server,
                              message)

    async def on_message_edit(self, before, after):
        # Ignore private messages
        if not after.server:
            return
        await self.send_event('MESSAGE_EDIT',
                              after.server,
                              before,
                              after)

    async def on_server_join(self, server):
        await self.send_event('GUILD_JOIN',
                              server,
                              server)

    async def on_server_remove(self, server):
        await self.send_event('GUILD_REMOVE',
                              server,
                              server)

    async def on_server_update(self, before, after):
        await self.send_event('GUILD_UPDATE',
                              after,
                              before,
                              after)

    async def on_member_join(self, member):
        await self.send_event('MEMBER_JOIN',
                              member.server,
                              member)

    async def on_member_remove(self, member):
        await self.send_event('MEMBER_REMOVE',
                              member.server,
                              member)
