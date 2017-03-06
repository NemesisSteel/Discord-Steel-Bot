from base import Base, Streamer

import os
import requests

class Hitbox(Base):

    sleep_time = 1
    chunk_size = 50
    platform_db_name = 'hitbox_streamers'

    def stream_to_streamer(self, streamer_info):
        streamer = Streamer()
        streamer.name = streamer_info['media_name']
        streamer.display_name = streamer_info['media_display_name']
        streamer.profile_url = streamer_info['channel']['channel_link']
        if streamer_info['user_logo']:
            streamer.avatar = 'https://edge.sf.hitbox.tv' + streamer_info['user_logo']
        else:
            streamer.avatar = 'https://edge.sf.hitbox.tv/static/img/generic/default-user-200.png'
        streamer.is_live = True
        streamer.stream_url = streamer_info['channel']['channel_link']
        streamer.stream_game = streamer_info['category_name'] or 'None'
        streamer.stream_id = streamer_info['media_id']
        streamer.stream_title = streamer_info['media_status']
        streamer.stream_preview = 'https://edge.sf.hitbox.tv' + streamer_info['media_thumbnail']
        streamer.stream_viewers_count = streamer_info['media_views']
        streamer.color = 0x99cc00
        streamer.platform_name = 'Hitbox'

        return streamer

    def get_streams(self, *streamers):
        URL = 'https://api.hitbox.tv/media/live/{}.json'.format(','.join(streamers))
        params = {'fast': 1,
                  'live_only': '1'}
        r = requests.get(URL, params=params)
        body = r.json()
        streams = body.get('livestream', [])
        # take only live
        streams = list(filter(lambda s: s['media_is_live'] != '0',
                              streams))
        return streams

app = Hitbox(redis_url=os.getenv('REDIS_URL'), discord_token=os.getenv('MEE6_TOKEN'))
app.run()
