class Channel:
    def __init__(self, channel):
        self.id = channel.get('id')
        self.name = channel.get('name')
        self.topic = channel.get('topic')
        self.position = channel.get('position')


class Role:
    def __init__(self, role):
        self.id = role.get('id')
        self.name = role.get('name')
        self.permissions = role.get('permissions')
        self.colour = role.get('colour')
        self.hoist = role.get('hoist')
        self.position = role.get('position')
        self.managed = role.get('managed')
        self.mentionable = role.get('mentionable')
        self.is_everyone = role.get('is_everyone')
        self.created_at = role.get('created_at')
        self.mention = role.get('mention')


class Member:
    def __init__(self, member):
        self.id = member.get('id')
        self.name = member.get('name')
        self.roles = list(map(Role, member.get('roles')))
        self.joined_at = member.get('joined_at')
        self.status = member.get('status')
        self.nick = member.get('nick')
        self.colour = member.get('colour')
        self.top_role = Role(member.get('top_role'))
        self.guild_permissions = member.get('guild_permissions')


class Guild:
    def __init__(self, guild):
        self.id = guild.get('id')
        self.name = guild.get('name')
        self.roles = list(map(Role, guild.get('roles')))
        self.owner = Member(guild.get('owner'))
        self.me = Member(guild.get('me'))
        self.large = guild.get('large')
        self.icon_url = guild.get('icon_url')
        self.member_count = guild.get('member_count')
        self.created_at = guild.get('created_at')
        self.default_channel = Channel(guild.get('default_channel'))
        self.channels = list(map(Channel, guild.get('channels')))


class Message:
    def __init__(self, message):
        self.id = message.get('id')
        self.edited_timestamp = message.get('edited_timestamp')
        self.tts = message.get('tts')
        self.author = Member(message.get('author'))
        self.content = message.get('content')
        self.channel = Channel(message.get('channel'))
        self.guild = Guild(message.get('guild'))
        self.mention_everyone = message.get('mention_everyone')
        self.pinned = message.get('pinned')
        self.clean_content = message.get('clean_content')

