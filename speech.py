import dataset
import logging
from settings import settings
from markovify import NewlineText
from cachetools.func import ttl_cache

logger = logging.getLogger(__name__)
db = dataset.connect(settings.DATABASE_URL)[settings.MESSAGES_TABLE_NAME]


@ttl_cache(ttl=settings.MODEL_CACHE_TTL)
def get_model(chat):
    logger.debug(f'fetching model for chat-id:{chat.id}')
    chat_messages = db.find_one(chat_id=chat.id)
    if chat_messages:
        text = chat_messages['text']
        text_limited = '\n'.join(text.splitlines()[-settings.MESSAGE_LIMIT:])
        return NewlineText(text_limited)


def update_model(chat, message):
    logger.debug(f'updating model for chat-id:{chat.id}')
    chat_messages = db.find_one(chat_id=chat.id) or {}
    db.upsert({
        'chat_id': chat.id,
        'text': '\n'.join([chat_messages.get('text', ''), message])
    }, ['chat_id'])


def delete_model(chat):
    logger.debug(f'deleting model for chat-id:{chat.id}')
    db.delete(chat_id=chat.id)
    get_model.cache_clear()


def flush():
    logger.debug('cleaning up models\' cache')
    get_model.cache_clear()


def new_message(chat):
    logger.debug(f'generating message for chat-id:{chat.id}')
    model = get_model(chat)
    if model:
        return model.make_sentence(tries=50)
    else:
        return 'i need more data'
