from mee6.plugins import Reddit

reddit = Reddit()

import redis
import time
import os

r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost'),
                   decode_responses=True)

guilds = reddit.get_guilds()
print('Got {} guilds'.format(len(guilds)))
time.sleep(3)

for guild in guilds:
    print('Guild {} patched'.format(guild.id))
    announcement_channel = r.get('Reddit.{}:display_channel'.format(guild.id))
    subs = list(r.smembers('Reddit.{}:subs'.format(guild.id)))

    patch_config = {'announcement_channel': announcement_channel or guild.id,
                    'subreddits': subs}
    reddit.patch_config(guild, patch_config)
