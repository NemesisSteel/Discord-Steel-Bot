from worker_bot import WorkerBot
from plugins.printer import Printer
from plugins.welcome import Welcome
from plugins.indexer import Indexer

import os

bot = WorkerBot(discord_token=os.getenv('MEE6_TOKEN'))
bot.load_plugin(Indexer)
bot.run()
