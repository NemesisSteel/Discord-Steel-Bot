import config
import psycopg2

from utils import timestamp_from_snowflake
from psycogreen.gevent import patch_psycopg
patch_psycopg()

def init_postgres():
    if config.INTERACTION_STATS_ENABLED:
        return psycopg2.connect(host=config.POSTGRES_HOST,
                                port=config.POSTGRES_PORT,
                                dbname=config.POSTGRES_DB,
                                user=config.POSTGRES_USER,
                                password=config.POSTGRES_PASSWORD)
    else:
        return None


class Interaction:

    db = init_postgres()

    def __init__(self, command, ctx, response=None, plugin_name=None):
        self.command = command
        self.ctx = ctx
        self.response = response
        self.plugin_name = plugin_name

    def save(self):
        if not self.db:
            return

        response = self.response

        id = self.ctx.message.id
        command_name = self.command.name
        guild_id = self.ctx.guild.id
        caller_id = self.ctx.message.author.id
        message_content = self.ctx.message.content
        message_timestamp = timestamp_from_snowflake(id)

        response_code = None
        response_sent_at = None
        if response:
            response_code = self.response.code
            response_sent_at = response.sent_at

        values = (id,
                  command_name,
                  guild_id,
                  caller_id,
                  message_content,
                  message_timestamp,
                  response_code,
                  response_sent_at)

        cur = self.db.cursor()
        query = 'INSERT INTO command_interactions values (%s, %s, %s, %s, %s,' \
                ' %s, %s, %s)'
        cur.execute(query, values)
        cur.commit()
        cur.close()
