from disco.types.message import (MessageEmbed, MessageEmbedField,
MessageEmbedFooter, MessageEmbedImage, MessageEmbedThumbnail,
MessageEmbedVideo, MessageEmbedAuthor)


class TextChannel:
    def __init__(self, channel):
        self.id = channel.get('id')
        self.name = channel.get('name')
        self.topic = channel.get('topic')
        self.position = channel.get('position')


class VoiceChannel:
    def __init__(self, channel):
        self.id = channel.get('id')
        self.name = channel.get('name')
        self.bitrate = channel.get('bitrate')
        self.user_limit = channel.get('user_limit')
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
        self.is_default = role.get('is_default')
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
        self.mention = member.get('mention')
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
        self.default_channel = TextChannel(guild.get('default_channel'))
        self.text_channels = list(map(TextChannel, guild.get('text_channels')))
        self.voice_channels = list(map(VoiceChannel, guild.get('voice_channels')))


class Message:
    def __init__(self, message):
        self.id = message.get('id')
        self.edited_timestamp = message.get('edited_timestamp')
        self.tts = message.get('tts')
        self.author = Member(message.get('author'))
        self.content = message.get('content')
        self.channel = TextChannel(message.get('channel'))
        self.guild = Guild(message.get('guild'))
        self.mention_everyone = message.get('mention_everyone')
        self.pinned = message.get('pinned')
        self.clean_content = message.get('clean_content')


class Embed(MessageEmbed):
    @classmethod
    def from_dict(cls, dct):
        e = cls()
        e.color = dct.get('color')
        e.title = dct.get('title')
        e.description = dct.get('description')
        e.url = dct.get('url')

        if dct.get('author'):
            auth = dct['author']
            author = MessageEmbedAuthor()
            author.name = auth.get('name')
            author.url = auth.get('url')
            author.icon_url = auth.get('icon_url')
            e.author = author

        if dct.get('thumbnail'):
            thumb = dct['thumbnail']
            thumbnail = MessageEmbedThumbnail()
            thumbnail.url = thumb.get('url')
            thumbnail.proxy_url = thumb.get('proxy_url')
            thumbnail.width = thumb.get('width')
            thumbnail.height = thumb.get('height')
            e.thumbnail = thumbnail

        if dct.get('image'):
            img = dct['image']
            image = MessageEmbedImage()
            image.url = img.get('url')
            image.proxy_url = img.get('proxy_url')
            e.image = image

        if dct.get('footer'):
            foot = dct['footer']
            footer = MessageEmbedFooter()
            footer.text = foot.get('text')
            e.footer = footer
        else:
            footer = MessageEmbedFooter()
            footer.text = 'Mee6'
            e.footer = footer

        for f in dct.get('fields', ()):
            field = MessageEmbedField()
            field.name = f.get('name')
            field.value = f.get('value')
            field.inline = f.get('inline')
            e.fields.append(field)

        return e

    @property
    def fail_safe_message(self):
        fs = ''
        e = self
        if e.title:
            fs += '**{}**\n'.format(e.title)
        if e.description:
            fs += '```\n' + e.description + '```\n'
        for f in e.fields:
            fs += '**{}:** {} \n'.format(f.name, f.value)
        if e.url:
            fs += '\n{}'.format(e.url)

        fs += "\n\n **TIP:** This message could be way" \
            "more beautiful if you give me the permission to post attachments " \
        "here 😇 "

        return fs
