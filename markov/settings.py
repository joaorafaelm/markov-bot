from decouple import config, Csv


class Settings:
    TELEGRAM_TOKEN = config('TELEGRAM_TOKEN', default='')
    ADMIN_USERNAMES = config('ADMIN_USERNAMES', default='', cast=Csv())
    SENTENCE_COMMAND = config('SENTENCE_COMMAND', default='sentence')
    REMOVE_COMMAND = config('REMOVE_COMMAND', default='remove')
    VERSION_COMMAND = config('VERSION_COMMAND', default='version')
    FLUSH_COMMAND = config('FLUSH_COMMAND', default='flush')
    HELP_COMMAND = config('HELP_COMMAND', default='help')
    START_COMMAND = config('START_COMMAND', default='start')
    DATABASE_URL = config('DATABASE_URL', default='sqlite:///:memory:')
    MODEL_CACHE_TTL = config('MODEL_CACHE_TTL', default='300', cast=int)
    COMMIT_HASH = config('HEROKU_SLUG_COMMIT', default='not set')
    MESSAGE_LIMIT = config('MESSAGE_LIMIT', default='5000', cast=int)
    LOG_LEVEL = config('LOG_LEVEL', default='INFO')
    ADMIN_CHAT_ID = config('ADMIN_CHAT_ID', default='')
    FILTERS = config('FILTERS', default='', cast=Csv())
    MODEL_LANG = config('MODEL_LANG', default='', cast=Csv())
    RETAIN_ORIG = config('RETAIN_ORIG', default=True, cast=bool)
    MAX_OVERLAP_RATIO = config('MAX_OVERLAP_RATIO', default=0.7, cast=float)
    TRIES = config('TRIES', default=50, cast=int)
    GROW_CHAIN = config('GROW_CHAIN', default=False, cast=bool)


settings = Settings()
