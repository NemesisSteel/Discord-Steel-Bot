from worker_bot import WorkerBot
from plugins.printer import Printer
from plugins.welcome import Welcome
from plugins.indexer import Indexer
from plugins.search import Search
from plugins.levels import Levels

import os

bot = WorkerBot()
bot.load_plugin(Indexer, Search, Levels)
bot.run()
