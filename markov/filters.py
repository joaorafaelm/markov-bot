import re
from markov.settings import settings

PATTERNS = {
    'email': r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
    'url': r'(https?|ftp)://[^\s/$.?#].[^\s]*'
}

filters = list(filter(None, [PATTERNS.get(f, '') for f in settings.FILTERS]))


def message_filter(message):
    if not message.text:
        return False

    return not any(re.search(f, message.text, re.I) for f in filters)
