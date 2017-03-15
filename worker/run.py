from worker_bot import WorkerBot
from plugins.printer import Printer
from plugins.welcome import Welcome
from plugins.indexer import Indexer
from plugins.search import Search

import os

bot = WorkerBot()
bot.load_plugin(Indexer, Search)
bot.run()
