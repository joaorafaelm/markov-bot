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

db = dataset.connect(DATABASE_URL)
bot = telebot.TeleBot(TELEGRAM_TOKEN)


@ttl_cache(ttl=MODEL_CACHE_TTL)
def get_model(chat):
    logger.info(f'fetching messages for {chat.title}')
    messages = db['messages']
    chat_messages = messages.find_one(chat_id=chat.id)
    if chat_messages:
        return markovify.text.NewlineText(chat_messages['text'])


@bot.message_handler(commands=[SENTENCE_COMMAND])
def sentence(message):
    chat_model = get_model(message.chat)
    generated_message = chat_model.make_sentence(
        max_overlap_ratio=0.7,
        tries=50
    ) if chat_model else None

    logger.info(f'generating message for {message.chat.title}')
    bot.send_message(
        message.chat.id,
        generated_message or 'i need more data'
    )


@bot.message_handler(commands=['remove'])
def admin(message):
    username = message.from_user.username
    chat_id = message.chat.id
    username_admins = [
        u.user.username for u in bot.get_chat_administrators(chat_id)
    ]

    if username in username_admins + ADMIN_USERNAMES:
        db['messages'].delete(chat_id=chat_id)
        get_model.cache_clear()
        bot.reply_to(message, 'messages deleted')
        logger.info(f'removing messages from {message.chat.title}')
        return

    bot.reply_to(message, 'u r not an admin 🤔')


@bot.message_handler(func=lambda m: True)
def messages(message):
    messages = db['messages']
    chat_messages = messages.find_one(chat_id=message.chat.id) or {}
    messages.upsert({
        'chat_id': message.chat.id,
        'chat_title': message.chat.title,
        'text': '\n'.join([chat_messages.get('text', ''), message.text])
    }, ['chat_id'])

    logger.info(f'saving message from {message.chat.title}')


if __name__ == '__main__':
    bot.polling(none_stop=True)
