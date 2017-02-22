from plugin import Plugin

import json

class Messages(Plugin):

    is_global = True

    async def on_message(self, m):
        message = dict(id=m.id,
                       ts=str(m.timestamp),
                       channel_id=m.channel.id,
                       channel_name=m.channel.name,
                       channel_topic=m.channel.topic,
                       server_id=m.server.id,
                       server_name=m.server.name,
                       author_id=m.author.id,
                       author_name=m.author.name,
                       author_discriminator=m.author.discriminator,
                       content=m.content,
                       clean_content=m.clean_content)
        await self.mee6.db.redis.lpush('mee6.messages', json.dumps(message))
