def parse_redis_url(redis_url):
    pattern = r'redis:\/\/([a-zA-Z0-9.]*):?([0-9]*)?'
    result = re.match(pattern, redis_url).groups()
    if result[1]:
        return (result[0], int(result[1]))
    return (result[0], 6379)

def fmt(raw_string, **mapping):
    result = raw_string
    for k, v in mapping.items():
        result = result.replace('{' + k + '}', str(v))

    return result

DISCORD_EPOCH = 1420070400000
def timestamp_from_snowflake(snowflake):
    return ((int(snowflake) >> 22) + DISCORD_EPOCH) / 1000
