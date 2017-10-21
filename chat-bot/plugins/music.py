import asyncio
import aiohttp
import os
import json
import functools
import discord
import logging

from sys import platform
from plugin import Plugin
from decorators import command
from collections import defaultdict

log = logging.getLogger('discord').info

if not discord.opus.is_loaded():
    if platform == "linux" or platform == "linux2":
        discord.opus.load_opus('./libopus.so')
    elif platform == "darwin":
        discord.opus.load_opus('libopus.dylib')

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

class Music(Plugin):

    fancy_name = "Music"
    buff_name = "music"
    players = dict()

    play_locks = defaultdict(asyncio.Lock)
    call_next = defaultdict(lambda: True)

    @command(pattern='^!play$',
             require_one_of_roles="allowed_roles",
             description="Makes me play the next song in the queue",
             usage='!play')
    async def play(self, m, args):
        voice = m.server.me.voice_channel
        if not voice:
            response = "I'm not connected to any voice channel :grimacing:..."
            return await self.mee6.send_message(m.channel, response)

        music = await self.pop_music(m.server)
        if not music:
            response = 'Nothing to play... :grimacing:'
            return await self.mee6.send_message(m.channel, response)

        try:
            await self._play(m.server, music)
        except Exception as e:
            response = 'An error occurred, sorry :grimacing:...'
            print(e)
            await self.mee6.send_message(m.channel, response)

    async def on_schwifty_finished_playing(self, guild_id):
        server = discord.Object(id=str(guild_id))
        music = await self.pop_music(server)
        if not music:
            return

        try:
            await self._play(server, music)
        except Exception as e:
            response = 'An error occurred, sorry :grimacing:...'
            print(e)


    @command(pattern='^!next$',
             description="Makes me jump to the next song in the queue",
             require_one_of_roles="allowed_roles",
             usage='!next')
    async def next(self, m, args):
        voice = m.server.me.voice_channel
        if not voice:
            response = "I'm not connected to any voice channel :grimacing:..."
            return await self.mee6.send_message(m.channel, response)

        music = await self.pop_music(m.server)
        if not music:
            response = 'Nothing to play... :grimacing:'
            return await self.mee6.send_message(m.channel, response)

        try:
            await self._play(m.server, music)
        except Exception as e:
            response = 'An error occurred, sorry :grimacing:...'
            print(e)
            await self.mee6.send_message(m.channel, response)

    @command(pattern='^!stop$',
             description="Makes me stop playing music",
             require_one_of_roles="allowed_roles",
             usage='!stop')
    async def stop(self, m, args):
        await self.mee6.schwifty.stop(m.server.id)

    async def _next(self, guild):
        music = await self.pop_music(guild)
        if not music:
            return

        voice = guild.voice_client
        if not voice:
            return

        try:
            await self._play(guild, music)
        except Exception as e:
            response = 'An error occurred, sorry :grimacing:...'
            print(e)
            print(response)

    async def _play(self, guild, music):
        await self.mee6.schwifty.play(guild.id, music['url'])
        await self.set_np(music, guild)

    async def __play(self, guild, music):
        lock = self.play_locks[guild.id]
        await lock.acquire()
        try:
            voice = guild.voice_client
            opts = {
             'default_search': 'auto',
             'quiet': True,
            }

            log('checkin curr_player')
            curr_player = self.players.get(guild.id)
            if curr_player:
                log(self.players)
                self.call_next[guild.id] = False
                log('stopping curr_player')
                curr_player.stop()
                log('curr player stopped')

            await self.set_np(music, guild)

            log('creating player')
            before_options = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 2'
            player = await voice.create_ytdl_player(music['url'],
                                                    ytdl_options=opts,
                                                    before_options=before_options,
                                                    after=self.sync_next(guild))
            log(player)
            log('player created')
            self.call_next[guild.id] = True
            self.players[guild.id] = player
            player.volume = 0.6
            log('starting player')
            player.start()
            log('player started')
        except Exception as e:
            log('An error occured in _play')
            log(str(e))
        finally:
            lock.release()

    @command(pattern='^!join',
             description="Makes me join your current voice channel",
             require_one_of_roles="allowed_roles",
             usage='!join')
    async def join(self, message, args):
        voice_channel = message.author.voice.voice_channel
        if not voice_channel:
            response = "You are not in a voice channel."
            return await self.mee6.send_message(message.channel, response)

        await self.mee6.schwifty.voice_connect(message.server.id)
        await self.mee6.ws.voice_state(message.server.id, voice_channel.id)

        response = "Connecting to voice channel **{}**".format(voice_channel.name)
        await self.mee6.send_message(message.channel, response)

    @command(pattern='^!leave',
             description='Makes me leave my current voice channel',
             require_one_of_roles="allowed_roles",
             usage='!leave')
    async def leave(self, message, args):
        await self.mee6.schwifty.voice_disconnect(message.server.id)
        await self.mee6.ws.voice_state(message.server.id, None, self_mute=True)

    @command(pattern='^!playlist$',
             description="Shows the songs in the playlist",
             require_one_of_roles="allowed_roles",
             usage='!playlist')
    async def playlist(self, message, args):
        response = ""
        storage = await self.get_storage(message.server)
        now_playing = await storage.get('now_playing')
        if now_playing:
            now_playing = json.loads(now_playing)
            np_fmt = "`NOW PLAYING` :notes: **{}** added by **{}**\n\n"
            response += np_fmt.format(now_playing.get('title'),
                                      now_playing['addedBy']['name'])

        queue = await storage.lrange('request_queue', 0, 5)
        for i, music_str in enumerate(queue[:5]):
            music = json.loads(music_str)
            fmt = "`#{}` **{}** added by **{}**\n"
            response += fmt.format(i + 1, music.get('title'),
                                   music['addedBy']['name'])

        fmt = "\n `Full playlist ` <https://mee6.xyz/request_playlist/{}>"
        response += fmt.format(message.server.id)

        await self.mee6.send_message(message.channel, response)

    @command(pattern='^!add (.*)',
             description="Adds a new song in the queue",
             require_one_of_roles="allowed_roles",
             usage='!add name_of_the_music')
    async def add(self, message, args):
        search = args[0]

        if 'http' in search:
            video_url = search
            # remove unecessary params
            video_url = video_url.split('&')[0]
        else:
            try:
                video_url = await self.get_yt_video_url(search)
            except Exception as e:
                response = "Didn't find any video :cry:!"
                return await self.mee6.send_message(message.channel,
                                                    response)

        try:
            info = await self.get_audio_info(video_url)
        except Exception as e:
            response = "An error occured, sorry :cry:..."
            return await self.mee6.send_message(message.channel,
                                                response)

        music = {"url": video_url,
                 "title": info.get('title', ''),
                 "thumbnail": ""}
        music["addedBy"] = {"name": message.author.name,
                            "discriminator": message.author.discriminator,
                            "avatar": message.author.avatar_url}

        await self.push_music(music, message.server)

        response = "**{}** added! :ok_hand:".format(music["title"])
        await self.mee6.send_message(message.channel, response)

    async def get_yt_video_url(self, search):
        url = "https://www.googleapis.com/youtube/v3/search"
        with aiohttp.ClientSession() as session:
            async with session.get(url, params={"type": "video",
                                                "q": search,
                                                "part": "snippet",
                                                "key": GOOGLE_API_KEY}) as resp:
                data = await resp.json()

        if not data.get("items"):
            raise Exception("An error occured")

        items = data["items"]
        if len(items) == 0:
            return None

        video_url = "https://youtube.com/watch?v=" + items[0]["id"]["videoId"]
        return video_url

    async def get_audio_info(self, url):
        import youtube_dl

        opts = {
            'format': 'webm[abr>0]/bestaudio/best',
            'prefer_ffmpeg': True
        }

        ydl = youtube_dl.YoutubeDL(opts)
        func = functools.partial(ydl.extract_info, url, download=False)
        info = await self.mee6.loop.run_in_executor(None, func)
        if "entries" in info:
            info = info['entries'][0]

        return info

    async def push_music(self, music, guild):
        storage = await self.get_storage(guild)
        return await storage.rpush("request_queue", json.dumps(music))

    async def set_np(self, music, guild):
        storage = await self.get_storage(guild)
        return await storage.set("now_playing", json.dumps(music))

    async def pop_music(self, guild):
        storage = await self.get_storage(guild)
        music_str = await storage.lpop("request_queue")

        if not music_str:
            return None

        return json.loads(music_str)
