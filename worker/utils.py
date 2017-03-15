from disco.types.message import (MessageEmbed, MessageEmbedField,
MessageEmbedFooter, MessageEmbedImage, MessageEmbedThumbnail,
MessageEmbedVideo, MessageEmbedAuthor)


def fmt(raw_string, **mapping):
    result = raw_string
    for k, v in mapping.items():
        result = result.replace('{' + k + '}', v)

    return result

def Embed(dct):
    e = MessageEmbed()
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

def get_fail_safe_message(e):
    fs = ''
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
