class Plugin:
    def __init__(self, bot):
        self.bot = bot

    def dispatch(self, event_name="", *args, **kwargs):
        try:
            handler = getattr(self, 'on_' + event_name)
            handler(*args, **kwargs)
        except AttributeError as e:
            pass
