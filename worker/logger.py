import logging

logging.basicConfig(level=logging.INFO)

class Logger:
    @property
    def log(self):
        return logging.getLogger(str(self)).info
