import telebot
import markovify
import dataset
from cachetools.func import ttl_cache
import logging
from settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = dataset.connect(settings.DATABASE_URL)['messages']
bot = telebot.TeleBot(settings.TELEGRAM_TOKEN)


def is_from_admin(message):
    username = message.from_user.username
    chat_id = str(message.chat.id)
    username_admins = [
        u.user.username for u in bot.get_chat_administrators(chat_id)
    ]
    return (username in username_admins + settings.ADMIN_USERNAMES)


@ttl_cache(ttl=settings.MODEL_CACHE_TTL)
def get_model(chat):
    logger.info(f'fetching messages for {chat.id}')
    chat_id = str(chat.id)
    chat_messages = db.find_one(chat_id=chat_id)
    if chat_messages:
        text = chat_messages['text']
        text_limited = '\n'.join(text.splitlines()[-settings.MESSAGE_LIMIT:])
        return markovify.text.NewlineText(text_limited, retain_original=False)


@bot.message_handler(commands=[settings.SENTENCE_COMMAND])
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
    if is_from_admin(message):
        chat_id = str(message.chat.id)
        db.delete(chat_id=chat_id)
        get_model.cache_clear()
        bot.reply_to(message, 'messages deleted')
        logger.info(f'removing messages from {chat_id}')
        return

    bot.reply_to(message, 'u r not an admin 🤔')


@bot.message_handler(commands=['version'])
def get_repo_version(message):
    hash_len = 7
    commit_hash = settings.COMMIT_HASH[:hash_len]
    bot.reply_to(message, commit_hash)


@bot.message_handler(commands=['flush'])
def flush_cache(message):
    if is_from_admin(message):
        get_model.cache_clear()
        bot.reply_to(message, 'cache cleared')
        logger.info('cache cleared')
        return
    bot.reply_to(message, 'u r not an admin 🤔')


@bot.message_handler(func=lambda m: True)
def handle_message(message):
    update_model(message)
    if bot.get_me().username in message.text:
        generate_sentence(message)


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
