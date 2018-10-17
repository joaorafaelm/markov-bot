from decouple import config, Csv


class Settings:
    TELEGRAM_TOKEN = config('TELEGRAM_TOKEN', default='')
    ADMIN_USERNAMES = config('ADMIN_USERNAMES', default='', cast=Csv())
    SENTENCE_COMMAND = config('SENTENCE_COMMAND', default='sentence')
    DATABASE_URL = config('DATABASE_URL', default='sqlite:///:memory:')
    MODEL_CACHE_TTL = config('MODEL_CACHE_TTL', default='300', cast=int)
    COMMIT_HASH = config('HEROKU_SLUG_COMMIT', default='not set')
    MESSAGE_LIMIT = config('MESSAGE_LIMIT', default='5000', cast=int)
    MESSAGES_TABLE_NAME = config('MESSAGES_TABLE_NAME', default='messages')
    LOG_LEVEL = config('LOG_LEVEL', default='INFO')
    ADMIN_CHAT_ID = config('ADMIN_CHAT_ID', default='')


settings = Settings()
