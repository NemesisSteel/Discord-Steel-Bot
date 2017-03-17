import os


BROKER_URL = os.getenv('BROKER_URL')
REDIS_URL = os.getenv('REDIS_URL')
IMGUR_ID = os.getenv('IMGUR_ID')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
MEE6_TOKEN = os.getenv('MEE6_TOKEN')
MAL_USERNAME = os.getenv('MAL_USERNAME')
MAL_PASSWORD = os.getenv('MAL_PASSWORD')

POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_USER')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'mee6')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'mee6')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'mee6')
