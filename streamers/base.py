import redis
import os
import disco
import requests
import logging
import time
import re
import gevent

from disco.types.message import (MessageEmbed, MessageEmbedField,
MessageEmbedFooter, MessageEmbedImage, MessageEmbedThumbnail,
MessageEmbedVideo, MessageEmbedAuthor)
from disco.client import Client, ClientConfig
from disco.api.http import APIException
from random import randint
from gevent import monkey

monkey.patch_all()

logging.basicConfig(level=logging.INFO)

def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

class Streamer(object):
    name=''
    display_name= ''
    profile_url=''
    avatar=''
    is_live=''
    stream_url=''
    stream_game=''
    stream_id=''
    stream_title=''
    stream_preview=''
    stream_viewers_count=''
    color=0x6441A4
    platform_name=''

    @property
    def dict(self):
        return dict(name=self.name,
                    display_name=self.display_name,
                    profile_url=self.profile_url,
                    avatar=self.avatar,
                    is_live=self.is_live,
                    stream_url=self.stream_url,
                    stream_game=self.stream_game,
                    stream_id=self.stream_id,
                    stream_title=self.stream_title,
                    stream_preview=self.stream_preview,
                    stream_viewers_count=self.stream_viewers_count,
                    color=self.color,
                    platform_name=self.platform_name)

    @property
    def embed(self):
        e = MessageEmbed()
        e.color = self.color
        e.title = self.stream_title
        e.url = self.stream_url

        author = MessageEmbedAuthor()
        author.name = self.display_name
        author.url = self.stream_url
        author.icon_url = self.avatar
        e.author = author

        thumbnail = MessageEmbedThumbnail()
        thumbnail.url = self.avatar
        thumbnail.proxy_url = self.avatar
        thumbnail.width, thumbnail.height = 100, 100
        e.thumbnail = thumbnail

        image = MessageEmbedImage()
        image.url = self.stream_preview + '?rand={}'.format(randint(0, 999999))
        e.image = image

        footer = MessageEmbedFooter()
        footer.text = self.platform_name
        e.footer = footer

        if self.stream_game:
            game_field = MessageEmbedField()
            game_field.name = 'Played Game'
            game_field.value = self.stream_game
            game_field.inline = True
            e.fields.append(game_field)

        if self.stream_viewers_count or self.stream_viewers_count == 0:
            viewers_field = MessageEmbedField()
            viewers_field.name = 'Viewers'
            viewers_field.value = str(self.stream_viewers_count)
            viewers_field.inline = True
            e.fields.append(viewers_field)

        return e

class Base:

    sleep_time=1
    platform_db_name=''
    platform_name=''
    chunk_size=1

    def __init__(self, **kwargs):
        self.db = redis.from_url(kwargs.get('redis_url'), decode_responses=True)

        discord_config = ClientConfig()
        discord_config.token = kwargs.get('discord_token')
        discord_client = Client(discord_config)
        self.api = discord_client.api

        self.log = logging.getLogger(self.__class__.__name__).info

    def announce(self, streamer, *guilds):
        for guild in guilds:
            check_key='Streamers.{}.check:{}'.format(guild, streamer.stream_url)
            check = str(streamer.stream_id) in self.db.smembers(check_key)
            if check:
                continue

            channel_key = 'Streamers.{}:announcement_channel'.format(guild)
            try:
                channel = int(self.db.get(channel_key) or guild)
            except ValueError:
                channel = guild

            message_key = 'Streamers.{}:announcement_msg'.format(guild)
            message = self.db.get(message_key)
            message_formatted = message.replace('{streamer}',
                                                streamer.name).replace('{link}',
                                                                       streamer.stream_url)
            embed = streamer.embed
            self.log('OUT {}#{} >> {}'.format(guild, channel, message_formatted))

            try:
                self.send_announce(guild, channel, message_formatted, embed)
                self.db.sadd(check_key, streamer.stream_id)
            except Exception as e:
                self.log('----')
                self.log('Error occured when sending update to {}#{} {}'.format(guild,
                                                                                channel,
                                                                                streamer.name))
                self.log(e.msg)
                self.log(e.content)
                self.log(e)
                self.log(streamer.dict)
                self.log('----')

    def send_announce(self, guild, channel, message, embed, retry=0):
        try:
            r = self.api.channels_messages_create(int(channel), message,
                                                  embed=embed)
        except APIException as e:
            # Unknows Channel
            if e.code == 10003 and retry < 1:
                self.send_announce(guild, guild, message, embed, retry=retry+1)
            else:
                raise e

    def process(self):
        streamers = self.db.smembers('Streamers.*:{}'.format(self.platform_db_name))
        # only take none empty streamers
        streamers = list(filter(lambda s: s, streamers))
        # try to extract some streamers
        def extract(streamer):
            if '/' not in streamer:
                return streamer
            return streamer.split('/')[-1]
        streamers = list(map(extract, streamers))
        # throw weird names
        check = lambda s: re.match(r'^[a-zA-Z0-9_\-]*$', s)
        streamers = list(filter(check, streamers))

        for streamers_chunk in chunks(list(streamers), self.chunk_size):
            # Collect streams infos
            try:
                streams = self.get_streams(*streamers_chunk)
                self.log('Getting streams {}'.format(','.join(streamers_chunk)))

                # Convert streams to streamer dict
                streamers = map(self.stream_to_streamer, streams)

                for streamer in streamers:
                    # Get subscribed guilds
                    is_plugin_enabled = lambda gid: self.db.sismember('plugins:{}'.format(gid),
                                                                      'Streamers')

                    key = 'Streamers.*:{}:{}:guilds'.format(self.platform_db_name, streamer.name)
                    subs = filter(is_plugin_enabled, self.db.smembers(key))

                    # Announce
                    gevent.spawn(self.announce, streamer, *subs)
            except Exception as e:
                self.log('An error occured :/')
                self.log(e)

            time.sleep(self.sleep_time)

    def run(self):
        while True:
            self.process()
