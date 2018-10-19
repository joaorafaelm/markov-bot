import re
from settings import settings

PATTERNS = {
    'email': r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
    'url': r'(https?|ftp)://[^\s/$.?#].[^\s]*'
}

filters = list(filter(None, [PATTERNS.get(f, '') for f in settings.FILTERS]))


def message_filter(message):
    return not any(re.search(f, message.text, re.I) for f in filters)
