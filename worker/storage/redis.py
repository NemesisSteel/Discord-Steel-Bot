class RedisStorage:
    def __init__(self, guild_id, plugin_name, redis):
        self.guild_id = guild_id
        self.plugin_name = plugin_name

        self.prefix = '{}.{}:'.format(plugin_name,
                                      guild_id)
        self.redis = redis

    def set(self, key, value, ex=None):
        key = self.prefix + key
        return self.redis.set(key, value, ex)

    def get(self, key):
        key = self.prefix + key
        return self.redis.get(key)

    def smembers(self, key):
        key = self.prefix + key
        return self.redis.smembers(key)

    def sadd(self, key, member, *members):
        key = self.prefix + key
        return self.redis.sadd(key, member, *members)
