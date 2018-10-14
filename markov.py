import telebot
import markovify
import dataset
from cachetools.func import ttl_cache
import logging
from settings import settings
import functools


logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

db = dataset.connect(
    settings.DATABASE_URL
)[settings.MESSAGES_TABLE_NAME]
bot = telebot.TeleBot(settings.TELEGRAM_TOKEN)


def admin_required(func):
    @functools.wraps(func)
    def wrapper_admin_required(message, *args, **kwargs):
        username = message.from_user.username
        chat_id = str(message.chat.id)
        username_admins = []
        if message.chat.type != 'private':
            username_admins = [
                u.user.username for u in bot.get_chat_administrators(chat_id)
            ]
        if username in username_admins + settings.ADMIN_USERNAMES:
            return func(message, *args, **kwargs)
        else:
            bot.reply_to(message, 'u r not an admin 🤔')
    return wrapper_admin_required


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
def generate_sentence(message, reply=False):
    chat_model = get_model(message.chat)
    generated_message = (chat_model.make_sentence(
        max_overlap_ratio=0.7,
        tries=50
    ) if chat_model else None) or 'i need more data'

    logger.info(f'generating message for {message.chat.id}')

    if reply:
        bot.reply_to(message, generated_message)
        return

    bot.send_message(
        message.chat.id,
        generated_message
    )


@bot.message_handler(commands=['remove'])
@admin_required
def remove_messages(message):
    if message.text.startswith('/remove'):
        markup = telebot.types.ReplyKeyboardMarkup(
            row_width=1, one_time_keyboard=True
        )
        markup.add('yes', 'no')
        reply = bot.reply_to(
            message, 'this operation will delete all data, are you sure?',
            reply_markup=markup
        )
        bot.register_next_step_handler(reply, remove_messages)

    elif message.text == 'yes':
        chat_id = str(message.chat.id)
        db.delete(chat_id=chat_id)
        get_model.cache_clear()
        bot.reply_to(message, 'messages deleted')
        logger.info(f'removing messages from {chat_id}')

    elif message.text == 'no':
        bot.reply_to(message, 'aborting then')


@bot.message_handler(commands=['version'])
def get_repo_version(message):
    hash_len = 7
    commit_hash = settings.COMMIT_HASH[:hash_len]
    bot.reply_to(message, commit_hash)


@bot.message_handler(commands=['flush'])
@admin_required
def flush_cache(message):
    get_model.cache_clear()
    bot.reply_to(message, 'cache cleared')
    logger.info('cache cleared')
    bot.reply_to(message, 'u r not an admin 🤔')


@bot.message_handler(func=lambda m: True)
def handle_message(message):
    update_model(message)
    if f'@{bot.get_me().username}' in message.text:
        generate_sentence(message, reply=True)


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
