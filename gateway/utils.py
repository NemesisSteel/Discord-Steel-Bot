from functools import wraps

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
                is_everyone=role.is_everyone,
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
                guild_pemissions=int(member.server_permissions.value))

@safe_none
def dump_channel(channel):
    return dict(id=channel.id,
                name=channel.name,
                topic=str(channel.topic),
                position=channel.position)

@safe_none
def dump_server(server):
    roles = list(map(dump_role, server.roles))
    owner = dump_member(server.owner)
    me = dump_member(server.me)
    default_channel = dump_channel(server.default_channel)
    channels = list(map(dump_channel,
                        server.channels))
    return dict(id=server.id,
                name=server.name,
                roles=roles,
                owner=owner,
                me=me,
                large=server.large,
                icon_url=server.icon_url,
                member_count=server.member_count,
                created_at=str(server.created_at),
                default_channel=default_channel,
                channels=channels)

@safe_none
def dump_message(message):
    return dict(id=message.id,
                edited_timestamp=str(message.edited_timestamp),
                timestamp=str(message.timestamp),
                tts=message.tts,
                author=dump_member(message.author),
                content=message.content,
                channel=dump_channel(message.channel),
                guild=dump_server(message.server),
                mention_everyone=message.mention_everyone,
                pinned=message.pinned,
                clean_content=message.clean_content)

SWITCHER = dict(Member=dump_member,
                Server=dump_server,
                Channel=dump_channel,
                Message=dump_message,
                Role=dump_role)
def dump(obj):
    model_name = obj.__class__.__name__
    return SWITCHER[model_name](obj)
