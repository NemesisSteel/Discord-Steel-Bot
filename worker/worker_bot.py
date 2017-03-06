import gevent
import gevent.monkey
import redis
import json
import logging

from time import time
from discord_types import Message, Guild, Member
from plugins.printer import Printer
from guild_storage import GuildStorage
from disco.client import Client, ClientConfig
from constants import EVENTS, TIMEOUT


logging.basicConfig(level=logging.INFO)

gevent.monkey.patch_all()

def parse_redis_url(redis_url):
    pattern = r'redis:\/\/([a-zA-Z0-9.]*):?([0-9]*)?'
    result = re.match(pattern, redis_url).groups()
    if result[1]:
        return (result[0], int(result[1]))
    return (result[0], 6379)

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

class WorkerBot(object):
    def __init__(self, *args, **kwargs):
        self.broker_url = kwargs.get('broker_url',
                                     'redis://localhost')
        self.redis_url = kwargs.get('redis_url',
                                    'redis://localhost')

        self.log = logging.getLogger('worker').info

        self.redis = redis.from_url(self.redis_url,
                                    decode_responses=True)
        self.log('Connected to redis database')

        discord_config = ClientConfig()
        discord_config.token = kwargs.get('discord_token')
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
        return filter(lambda p: p.__class__.__name__ in enabled_plugins or \
                      p.__global__,
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
            guild.storage = GuildStorage(guild.id,
                                         plugin.__class__.__name__,
                                         self.redis)
            if data:
                plugin.dispatch(event_name, guild, data)
            elif before:
                plugin.dispatch(event_name, guild, before, after)
            else:
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

    def run(self):
        for _ in range(1, LISTENERS_COUNT + 1):
            conn = self.broker_connection()

            listener = self.listener_fact()
            self.listeners.append(gevent.spawn(listener))
            self.log('Starting listener {}-{}'.format(_, LISTENERS_COUNT))

        gevent.joinall(self.listeners)

