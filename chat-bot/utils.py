import re
import operator

### REDIS URL PARSER

def parse_redis_url(redis_url):
    pattern = r'redis:\/\/([a-zA-Z0-9.]*):?([0-9]*)?'
    result = re.match(pattern, redis_url).groups()
    if result[1]:
        return (result[0], int(result[1]))
    else:
        return (result[0], 6379)

### DATE FORMATTER

def format_date(d): return d and d.strftime("%Y-%m-%d %H:%M:%S")

### RICH_RESPONSE POPULATER

class RichEntity:
    def _get_fields(self):
        return [field for field in dir(self) if not field.startswith('_')]

    def _get_pattern(self):
        fields = self._get_fields()
        name = self._entity_name

        pattern_vars = []
        for field in fields:
            group_name = name + '__' + field
            path = name + '.' + field
            pattern_vars.append('({' + path + '})')

        pattern_vars.append('({' + name + '})')

        return '|'.join(pattern_vars)

class RichUser(RichEntity):
    _entity_name = 'user'

    def __init__(self, user):
        self.name = user.name
        self.discriminator = user.discriminator
        self.id = user.id
        self.mention = user.mention
        self.joined_at = format_date(user.joined_at)
        self.created_at = format_date(user.created_at)
        self.status = str(user.status)
        self.isbot = str(user.bot)
        self.picture = user.avatar_url
        self.nickname = user.display_name

    def __str__(self): return self.mention

class RichChannel(RichEntity):
    _entity_name = 'channel'

    def __init__(self, channel):
        self.name = channel.name
        self.mention = channel.mention
        self.id = channel.id
        self.topic = channel.topic
        self.position = int(channel.position or 0) + 1
        self.created_at = format_date(channel.created_at)

    def __str__(self): return self.mention

class RichServer(RichEntity):
    _entity_name = 'server'

    def __init__(self, server):
        self.name = server.name
        self.region = server.region
        self.afk_timeout = server.afk_timeout
        self.afk_channel = server.afk_channel and server.afk_channel.name
        self.afk_channel_mention = server.afk_channel and server.afk_channel.mention

        icon = "https://cdn.discordapp.com/icons/{}/{}.webp".format(server.id,
                                                                    server.icon)
        self.icon = server.icon and icon
        self.member_count = server.member_count
        self.created_at = format_date(server.created_at)

class Dummy():
    def __getattr__(self, attrname): return None

def _build_re():
    dummy = Dummy()
    user_pattern = RichUser(dummy)._get_pattern()
    channel_pattern = RichChannel(dummy)._get_pattern()
    server_pattern = RichServer(dummy)._get_pattern()

    pattern = '|'.join([user_pattern, channel_pattern, server_pattern])
    return re.compile(pattern)

class Context:
    def __init__(self, user=None, server=None, channel=None, message=None):
        if message:
            self.user = RichUser(message.author)
            self.server = message.server
            self.channel = message.channel

        if user: self.user = RichUser(user)
        if server: self.server = server
        if channel: self.channel = channel

REX = _build_re()

def repl(context, match):
    field = next(field for field in match.groups() if field)
    try:
        field_value = operator.attrgetter(field[1:-1])(context)
    except AttributeError:
        field_value = field

    return str(field_value)

def rich_response(response, **kwargs):
    context = Context(**kwargs)
    return REX.sub(lambda m: repl(context, m), response)

