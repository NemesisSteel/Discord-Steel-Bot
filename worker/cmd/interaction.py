import config
import psycopg2

from utils import timestamp_from_snowflake
from psycogreen.gevent import patch_psycopg
patch_psycopg()


class Interaction:

    db = psycopg2.connect(host=config.POSTGRES_HOST,
                          port=config.POSTGRES_PORT,
                          dbname=config.POSTGRES_DB,
                          user=config.POSTGRES_USER,
                          password=config.POSTGRES_PASSWORD)

    def __init__(self, command, ctx, response=None):
        self.command = command
        self.ctx = ctx
        self.response = response

    def save(self):
        response = self.response

        id = self.ctx.message.id
        command_name = self.command.command_name
        guild_id = self.ctx.guild.id
        caller_id = self.ctx.message.author.id
        message_content = self.ctx.message.content
        message_timestamp = timestamp_from_snowflake(id)

        response_message = None
        response_embed = None
        response_sent = False
        response_sent_at = None
        if response:
            response_message = response.message
            response_fail_safe_message = response.fail_safe_message
            response_sent_at = response.sent_at

        values = (id,
                  command_name,
                  guild_id,
                  caller_id,
                  message_content,
                  response_message,
                  response_embed,
                  response_sent_at)

        cur = self.db.cursor()
        query = 'INSERT INTO command_interactions values (%s, %s, %s, %s, %s,' \
                ' %s, %s, %s)'
        cur.execute(query, values)
        cur.commit()
        cur.close()
