import gevent
import gevent.monkey
import redis
import json
import logging

from time import time

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
          'GUILD_JOIN',
          'GUILD_REMOVE',
          'GUILD_UPDATE',
          'MEMBER_JOIN',
          'MEMBER_REMOVE'}

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

        self.listeners = []

    def broker_connection(self):
        return redis.from_url(self.broker_url,
                              decode_responses=True)

    def get_dispatch(self, event_name, payload):
        def _dispatch():
            self.dispatch(event_name, payload)
        return _dispatch

    def dispatch(self, event_name, payload):
        guild = payload['g']
        timestamp = payload['ts']

        data = payload.get('d')
        before = payload.get('b')
        after = payload.get('a')

        diff = time() - timestamp
        self.log('Received {} +{}'.format(event_name, diff))

    def listener_fact(self):
        keys = list(map(lambda e: 'discord.events.{}'.format(e),
                        EVENTS))
        conn = self.broker_connection()
        def loop():
            while True:
                queue, data = conn.brpop(keys)
                if data:
                    event_name = queue.split('.')[-1]
                    data = json.loads(data)
                    gevent.spawn(self.get_dispatch(event_name, data))
                gevent.sleep(0.01)

        return loop

    def run(self):
        for _ in range(1, LISTENERS_COUNT + 1):
            conn = self.broker_connection()

            listener = self.listener_fact()
            self.listeners.append(gevent.spawn(listener))
            self.log('Starting listener {}-{}'.format(_, LISTENERS_COUNT))

        gevent.joinall(self.listeners)


