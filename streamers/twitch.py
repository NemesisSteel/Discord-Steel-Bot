from base import Base, Streamer

import os
import requests

TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')

class Twitch(Base):

    sleep_time = 1
    chunk_size = 100
    platform_db_name = 'streamers'

    def stream_to_streamer(self, streamer_info):
        streamer = Streamer()
        streamer.name = streamer_info['channel']['name']
        streamer.display_name = streamer_info['channel']['display_name']
        streamer.profile_url = streamer_info['channel']['url']
        streamer.avatar = streamer_info['channel']['logo']
        streamer.is_live = True
        streamer.stream_url = streamer_info['channel']['url']
        streamer.stream_game = streamer_info['game']
        streamer.stream_id = streamer_info['_id']
        streamer.stream_title = streamer_info['channel']['status']
        streamer.stream_preview = streamer_info['preview']['medium']
        streamer.stream_viewers_count = streamer_info['viewers']
        streamer.color = 0x6441A4
        streamer.platform_name = 'Twitch'

        return streamer

    def get_streams(self, *streamers):
        URL = 'https://api.twitch.tv/kraken/streams'
        params = {'client_id': TWITCH_CLIENT_ID,
                  'channel': ','.join(streamers),
                  'limit': 100}
        r = requests.get(URL, params=params)
        body = r.json()
        streams = body['streams']
        return streams

app = Twitch(redis_url=os.getenv('REDIS_URL'), discord_token=os.getenv('MEE6_TOKEN'))
app.run()
