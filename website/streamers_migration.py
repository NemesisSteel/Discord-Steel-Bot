import os
import redis

redis_url = os.getenv('REDIS_URL', 'redis://localhost')
db = redis.from_url(redis_url, decode_responses=True) 

predicate = lambda s: db.sismember('plugins:{}'.format(s), 'Streamers')
servers = list(filter(predicate, db.smembers('servers')))

for server_id in servers:
    STREAMERS_TYPES = ('streamers', 'hitbox_streamers', 'beam_streamers')
    for s_type in STREAMERS_TYPES:
        key = 'Streamers.{}:{}'.format(server_id, s_type)
        new_streamers = list(db.smembers(key))

        # add every new streamer to guild
        db.sadd(key, *new_streamers)

        # add new_streamers to streamers list
        key = 'Streamers.*:{}'.format(s_type)
        db.sadd(key, *new_streamers)

        key_fmt = 'Streamers.*:{}'.format(s_type)
        key_fmt = key_fmt + ':{}:guilds'

        # add guild to every new streamer guild list
        for streamer in new_streamers:
            db.sadd(key_fmt.format(streamer), server_id)

print('{} guilds [OK]'.format(len(servers)))
