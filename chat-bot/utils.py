import re

def parse_redis_url(redis_url):
    pattern = r'redis:\/\/([a-zA-Z0-9.]*):?([0-9]*)?'
    result = re.match(pattern, redis_url).groups()
    if result[1]:
        return (result[0], int(result[1]))
    else:
        return (result[0], 6379)


def variables(res, message):
    # res is short for response, in oder to keep under 80 char a line
    res = uservars(res, message.author)
    res = servervars(res, message.server)
    res = channelvars(res, message.channel)
    return res


    # user information
def uservars(res, user):
    if "{user" in res: # only if needed
        res = res.replace('{user.name}', user.name)
        res = res.replace('{user.discriminator}', user.discriminator)
        res = res.replace('{user.id}', user.id)
        res = res.replace('{user}', user.mention)
        res = res.replace('{user.mention}', user.mention)
        roles = ""
        for role in user.roles:
            roles = roles + role.name + ", "
        roles = roles.replace('@', '')
        roles = roles[:-2]
        res = res.replace('{user.roles}', roles)
        res = res.replace('{user.joined_at}',
            user.joined_at.strftime("%Y-%m-%d %H:%M:%S"))
        res = res.replace('{user.created_at}',
            user.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        res = res.replace('{user.status}', str(user.status))
        res = res.replace('{user.isbot}', str(user.bot))
        res = res.replace('{user.pictureURL}', user.avatar_url)
        res = res.replace('{user.nickname}', user.display_name)
    return res
    #server information
def servervars(res, server):
    if "{server" in res:
        res = res.replace('{server}', server.name)
        res = res.replace('{server.name}', server.name)
        emojis = ""
        for emoji in server.emojis:
            emojis = emojis + "<:" + emoji.name + ":" + emoji.id + "> "
        res = res.replace('{server.emojis}', emojis)
        res = res.replace('{server.region}', str(server.region))
        res = res.replace('{server.afk.timeout}', str(server.afk_timeout))
        if (server.afk_channel != None):
            res = res.replace('{server.afk.channel}', server.afk_channel.name)
        else:
            res = res.replace('{server.afk.channel}', "no afk channel")
        res = res.replace('{server.id}', server.id)
        if server.icon:
            res = res.replace('{server.icon}',
                "https://cdn.discordapp.com/icons/" +
                server.id + "/" + server.icon + ".webp")
        else:
            res=res.replace('{server.icon}', "no server icon found")
        owner = "@" + server.owner.name + "#" + server.owner.discriminator
        res = res.replace('{server.owner}', owner)
        res = res.replace('{server.membercount}', str(server.member_count))
        res = res.replace('{server.created_at}',
            server.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        res = res.replace('{server.channels.default}',
            "<#"+server.default_channel.id+">")
        res = res.replace('{server.verification_level}',
            str(server.verification_level))
    return res
#channel info
def channelvars(res, channel):
    if "{channel" in res:
        res = res.replace('{channel.name}', channel.name)
        res = res.replace('{channel}', channel.mention)
        res = res.replace('{channel.mention}', channel.mention)
        res = res.replace('{channel.id}', channel.id)
        res = res.replace('{channel.topic}', channel.topic)
        res = res.replace('{channel.position}', str(channel.position + 1))
        res = res.replace('{channel.created_at}',
            channel.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    return res
