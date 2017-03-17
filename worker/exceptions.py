class BotException(Exception):
    message = "An error occured in Mee6 land 🤒 "

class NotFound(BotException):
    message = "Sorry I didn't find anything 😭 "
