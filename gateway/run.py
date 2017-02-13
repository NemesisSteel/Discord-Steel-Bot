from gateway_bot import GatewayBot

import os

TOKEN = os.getenv('MEE6_TOKEN')
BROKER_URL = os.getenv('BROKER_URL', 'redis://localhost')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost')
SHARD_ID = int(os.getenv('SHARD_ID', 0))
SHARD_COUNT = int(os.getenv('SHARD_COUNT', 1))

bot = GatewayBot(shard_id=SHARD_ID,
                 shard_count=SHARD_COUNT,
                 broker_url=BROKER_URL,
                 redis_url=REDIS_URL)
bot.run(TOKEN)
