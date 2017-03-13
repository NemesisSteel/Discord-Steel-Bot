import re

from functools import wraps

def find(predicate, iterable):
    return next(filter(predicate, iterable), None)

def parse_redis_url(redis_url):
	pattern = r'redis:\/\/([a-zA-Z0-9.]*):?([0-9]*)?'
	result = re.match(pattern, redis_url).groups()

	if result[1]:
		return (result[0], int(result[1]))

	return (result[0], 6379)

def safe_none(f):
    @wraps(f)
    def decorated(obj):
        if not obj:
            return None
        return f(obj)
    return decorated

@safe_none
def dump_role(role):
    return dict(id=role.id,
                name=role.name,
                permissions=int(role.permissions.value),
                colour=role.colour.value,
                hoist=role.hoist,
                position=role.position,
                managed=role.managed,
                mentionable=role.mentionable,
                is_default=role.is_default(),
                created_at=str(role.created_at),
                mention=role.mention)

@safe_none
def dump_member(member):
    roles = list(map(dump_role, member.roles))
    top_role = dump_role(member.top_role)
    return dict(id=member.id,
                name=member.name,
                roles=roles,
                joined_at=str(member.joined_at),
                status=str(member.status),
                nick=member.nick,
                colour=member.colour.value,
                top_role=top_role,
                mention=member.mention,
                guild_permissions=int(member.guild_permissions.value))

@safe_none
def dump_text_channel(channel):
    return dict(id=channel.id,
                name=channel.name,
                topic=channel.topic,
                position=channel.position)

@safe_none
def dump_voice_channel(channel):
    return dict(id=channel.id,
                name=channel.name,
                bitrate=channel.bitrate,
                user_limit=channel.user_limit,
                position=channel.position)

@safe_none
def dump_guild(guild):
    roles = list(map(dump_role, guild.roles))
    owner = dump_member(guild.owner)
    me = dump_member(guild.me)
    default_channel = dump_text_channel(guild.default_channel)
    voice_channels = list(map(dump_voice_channel,
                              guild.voice_channels))
    text_channels = list(map(dump_text_channel,
                             guild.text_channels))
    return dict(id=guild.id,
                name=guild.name,
                roles=roles,
                owner=owner,
                me=me,
                large=guild.large,
                icon_url=guild.icon_url,
                member_count=guild.member_count,
                created_at=str(guild.created_at),
                default_channel=default_channel,
                voice_channels=voice_channels,
                text_channels=text_channels)

@safe_none
def dump_message(message):
    return dict(id=message.id,
                edited_timestamp=str(message.edited_timestamp),
                tts=message.tts,
                author=dump_member(message.author),
                content=message.content,
                channel=dump_text_channel(message.channel),
                guild=dump_guild(message.guild),
                mention_everyone=message.mention_everyone,
                pinned=message.pinned,
                clean_content=message.clean_content)

SWITCHER = dict(Member=dump_member,
                Guild=dump_guild,
                VoiceChannel=dump_voice_channel,
                TextChannel=dump_text_channel,
                Message=dump_message,
                Role=dump_role)

def dump(obj):
    model_name = obj.__class__.__name__
    return SWITCHER[model_name](obj)
