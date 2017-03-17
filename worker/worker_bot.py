import gevent
import gevent.monkey
import redis
import json
import logging
import os
import config

from time import time
from discord.types import Message, Guild, Member, TextChannel, Embed
from disco.api.http import APIException
from plugins.printer import Printer
from storage.redis import RedisStorage
from disco.client import Client, ClientConfig
from constants import EVENTS, TIMEOUT
from utils import parse_redis_url


logging.basicConfig(level=logging.INFO)

gevent.monkey.patch_all()

EVENTS = {'MESSAGE_CREATE',
          'MESSAGE_DELETE',
          'MESSAGE_EDIT',
          'GUILD_READY',
          'GUILD_JOIN',
          'GUILD_REMOVE',
          'GUILD_UPDATE',
          'MEMBER_JOIN',
          'MEMBER_REMOVE'}

TYPES = {'MESSAGE': Message,
         'GUILD': Guild,
         'MEMBER': Member}

LISTENERS_COUNT = 100

DEFAULT_BROKER_URL = 'redis://localhost'
DEFAULT_REDIS_URL = 'redis://localhost'

class WorkerBot(object):
    def __init__(self, *args, **kwargs):
        self.broker_url = config.BROKER_URL or DEFAULT_BROKER_URL
        self.redis_url = config.REDIS_URL or DEFAULT_BROKER_URL

        self.log = logging.getLogger('worker').info

        self.redis = redis.from_url(self.redis_url,
                                    decode_responses=True)
        self.log('Connected to redis database')

        discord_config = ClientConfig()
        discord_config.token = config.MEE6_TOKEN
        discord_client = Client(discord_config)
        self.api = discord_client.api

        self.listeners = []
        self.plugins = []

    def load_plugin(self, *plugins):
        """ Loads plugins """
        for Plugin in plugins:
            fmt = 'Plugin {} loaded'
            self.log(fmt.format(Plugin.__name__))

            self.plugins.append(Plugin(self))

    def broker_connection(self):
        """ Gets a broker connection """
        return redis.from_url(self.broker_url,
                              decode_responses=True)

    def get_plugins(self, guild):
        enabled_plugins = self.redis.smembers('plugins:{}'.format(guild.id))
        return filter(lambda p: p.name in enabled_plugins or \
                      hasattr(p, '__global__'),
                      self.plugins)

    def cast(self, o_type):
        def caster(data):
            if data is None:
                return None
            return o_type(data)
        return caster

    def dispatch(self, event_name, payload):
        """ Dispatches events to plugins & co """
        o_type = TYPES[event_name.split('_')[0]]
        cast = self.cast(o_type)

        guild = Guild(payload['guild'])
        timestamp = payload['ts']

        data = cast(payload.get('data'))
        before = cast(payload.get('before'))
        after = cast(payload.get('after'))

        diff = time() - timestamp
        self.log('Received {} +{}'.format(event_name, diff))
        if diff > TIMEOUT:
            self.log('Droping {}'.format(event_name, diff))
            return


        enabled_plugins = list(self.get_plugins(guild))
        for plugin in enabled_plugins:
            guild.storage = RedisStorage(guild.id,
                                         plugin.name,
                                         self.redis)
            if data:
                plugin.dispatch(event_name, guild, data)
            if before:
                plugin.dispatch(event_name, guild, before, after)
            if not data and not before:
                plugin.dispatch(event_name, guild)

    def listener_fact(self):
        """ Returns a listener that'll listen to every event type """
        keys = list(map(lambda e: 'discord.events.{}'.format(e),
                        EVENTS))
        conn = self.broker_connection()
        def loop():
            while True:
                queue, data = conn.brpop(keys)
                if data:
                    event_name = queue.split('.')[-1]
                    data = json.loads(data)
                    gevent.spawn(self.dispatch, event_name, data)

        return loop

    def send_message(self, destination, message="", embed=None):
        """ Sends a message to a destination. Accepts member,
            text channel, guild, or snowflake destination.
        """
        ACCEPTED_DESTINATIONS = [int, TextChannel, Member, Guild]
        if destination.__class__ not in ACCEPTED_DESTINATIONS:
            return

        if hasattr(destination, 'id'):
            destination = destination.id

        if embed and embed.__class__ == dict:
            embed = Embed(embed)

        try:
            r = self.api.channels_messages_create(destination, message,
                                                  embed=embed)
        except APIException as e:
            # catch embed disabled
            if e.code in (50004, 50013) and embed:
                r = self.api.channels_messages_create(destination,
                                                      embed.fail_safe_message)
            else:
                raise e


    def run(self):
        for _ in range(1, LISTENERS_COUNT + 1):
            conn = self.broker_connection()

            listener = self.listener_fact()
            self.listeners.append(gevent.spawn(listener))
        self.log('Started {} listeners'.format(LISTENERS_COUNT))

        gevent.joinall(self.listeners)

