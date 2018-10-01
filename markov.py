import telebot
import markovify
from os import environ
import dataset
from cachetools.func import ttl_cache
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


TELEGRAM_TOKEN = environ.get('TELEGRAM_TOKEN')
ADMIN_USERNAMES = environ.get('ADMIN_USERNAMES', default='').split(',')
SENTENCE_COMMAND = environ.get('SENTENCE_COMMAND', default='sentence')
DATABASE_URL = environ.get('DATABASE_URL', default='sqlite:///:memory:')
MODEL_CACHE_TTL = int(environ.get('MODEL_CACHE_TTL', default='300'))

db = dataset.connect(DATABASE_URL)['messages']
bot = telebot.TeleBot(TELEGRAM_TOKEN)


@ttl_cache(ttl=MODEL_CACHE_TTL)
def get_model(chat):
    logger.info(f'fetching messages for {chat.id}')
    chat_id = str(chat.id)
    chat_messages = db.find_one(chat_id=chat_id)
    if chat_messages:
        return markovify.text.NewlineText(chat_messages['text'])


@bot.message_handler(commands=[SENTENCE_COMMAND])
def generate_sentence(message):
    chat_model = get_model(message.chat)
    generated_message = chat_model.make_sentence(
        max_overlap_ratio=0.7,
        tries=50
    ) if chat_model else None

    logger.info(f'generating message for {message.chat.id}')
    bot.send_message(
        message.chat.id,
        generated_message or 'i need more data'
    )


@bot.message_handler(commands=['remove'])
def remove_messages(message):
    username = message.from_user.username
    chat_id = str(message.chat.id)
    if username in ADMIN_USERNAMES:
        db.delete(chat_id=chat_id)
        get_model.cache_clear()
        bot.reply_to(message, 'messages deleted')
        logger.info(f'removing messages from {chat_id}')
        return

    bot.reply_to(message, 'u r not an admin 🤔')


@bot.message_handler(func=lambda m: True)
def update_model(message):
    chat_id = str(message.chat.id)
    chat_messages = db.find_one(chat_id=chat_id) or {}
    db.upsert({
        'chat_id': chat_id,
        'text': '\n'.join([chat_messages.get('text', ''), message.text])
    }, ['chat_id'])

    logger.info(f'saving message from {chat_id}')


if __name__ == '__main__':
    logger.info(f'starting the bot')
    bot.polling(none_stop=True)
