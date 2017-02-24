from worker_bot import WorkerBot
from plugins.printer import Printer

bot = WorkerBot()
bot.load_plugin(Printer)
bot.run()
