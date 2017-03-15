from plugin import Plugin
from elasticsearch import Elasticsearch

import os
import json
import gevent
import gevent.queue
import elasticsearch

def dump_member(member):
    data = dict(id=member.id,
                name=member.name,
                joined_at=member.joined_at,
                status=member.status,
                nick=member.nick,
                guild_permissions=member.guild_permissions)
    return data

def dump_text_channel(channel):
    data = dict(id=channel.id,
                name=channel.name,
                topic=channel.topic,
                position=channel.position)
    return data

def dump_voice_channel(channel):
    data = dict(id=channel.id,
                name=channel.name,
                bitrate=channel.bitrate,
                user_limit=channel.user_limit,
                position=channel.position)
    return data

def dump_guild(guild):
    data = dict(id=guild.id,
                name=guild.name,
                owner=dump_member(guild.owner),
                me=dump_member(guild.me),
                text_channels=list(map(dump_text_channel, guild.text_channels)),
                voice_channels=list(map(dump_voice_channel,
                                        guild.voice_channels)),
                large=guild.large,
                icon_url=guild.icon_url,
                member_count=guild.member_count,
                created_at=guild.created_at)
    return data

ES_URL = os.getenv('ES_URL')

class Indexer(Plugin):

    __global__ = True
    es = Elasticsearch([ES_URL])
    guild_index_queue = gevent.queue.Queue()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        gevent.spawn(self.guild_index_queue_consumer)

    def guild_index_queue_consumer(self):
        while True:
            guild = self.guild_index_queue.get(block=True)
            data = dump_guild(guild)
            self.log('Indexing guild {}'.format(guild.id))
            self.es.index(index='discord',
                          doc_type='guild',
                          id=int(guild.id),
                          body=data)

    def index_guild(self, guild):
        print('putting guiold to queue')
        self.guild_index_queue.put(guild)

    def on_guild_ready(self, guild):
        self.index_guild(guild)

    def on_guild_update(self, guild, before, after):
        self.index_guild(after)

    def on_guild_join(self, guild):
        self.index_guild(guild)

    def on_guild_remove(self, guild):
        self.index_guild(guild)
