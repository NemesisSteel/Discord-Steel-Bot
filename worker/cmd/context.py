class Context(object):
    @classmethod
    def from_message(cls, message):
        return cls(message=message,
                   guild=message.guild)

    def __init__(self, message=None, guild=None):
        self.message = message
        self.guild = guild

