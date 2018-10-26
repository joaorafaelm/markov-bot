import telebot
import markovify
import dataset
import logging
import functools
from cachetools.func import ttl_cache
from settings import settings
from filters import message_filter


logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

db = dataset.connect(settings.DATABASE_URL)[settings.MESSAGES_TABLE_NAME]
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


def confirmation_required(func):
    @functools.wraps(func)
    def wrapper_confirmation_required(message, *args, **kwargs):
        if message.text.startswith('/'):
            markup = telebot.types.ReplyKeyboardMarkup(
                row_width=1, one_time_keyboard=True, selective=True
            )
            markup.add('yes', 'no')
            reply = bot.reply_to(
                message, 'are you sure?',
                reply_markup=markup
            )
            logger.info(f'sending confirmation keyboard to {func.__name__}')
            callback = globals()[func.__name__]
            bot.register_next_step_handler(reply, callback)
            return

        elif message.text == 'yes':
            logger.info(f'received positive confirmation for {func.__name__}')
            func(message, *args, **kwargs)

        logger.info('removing keyboard')
        markup = telebot.types.ReplyKeyboardRemove()
        bot.reply_to(message, 'okay', reply_markup=markup)

    return wrapper_confirmation_required


@ttl_cache(ttl=settings.MODEL_CACHE_TTL)
def get_model(chat):
    logger.info(f'fetching messages for {chat.id}')
    chat_id = str(chat.id)
    chat_messages = db.find_one(chat_id=chat_id)
    if chat_messages:
        text = chat_messages['text']
        text_limited = '\n'.join(text.splitlines()[-settings.MESSAGE_LIMIT:])
        return markovify.text.NewlineText(text_limited)


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


@bot.message_handler(commands=[settings.REMOVE_COMMAND])
@admin_required
@confirmation_required
def remove_messages(message):
    chat_id = str(message.chat.id)
    db.delete(chat_id=chat_id)
    get_model.cache_clear()
    logger.info(f'removing messages from {chat_id}')


@bot.message_handler(commands=[settings.VERSION_COMMAND])
def get_repo_version(message):
    hash_len = 7
    commit_hash = settings.COMMIT_HASH[:hash_len]
    bot.reply_to(message, commit_hash)


@bot.message_handler(commands=[settings.FLUSH_COMMAND])
@admin_required
@confirmation_required
def flush_cache(message):
    get_model.cache_clear()
    logger.info('cache cleared')


@bot.message_handler(commands=[settings.HELP_COMMAND])
def help(message):
    help_text = (
        f'Welcome to MarkovBot, a Telegram bot that writes like you do using '
        'Markov chains!\n\n'
        '{settings.SENTENCE_COMMAND}: MarkovBot will generate a message.\n'
        '{settings.REMOVE_COMMAND}: MarkovBot will remove messages from chat.'
        '\n'
        '{settings.VERSION_COMMAND}: MarkovBot will state its current version'
        '.\n'
        '{settings.FLUSH_COMMAND}: MarkovBot will clear its cache.\n'
        '{settings.HELP_COMMAND}: MarkovBot will print this help message!'
    )
    bot.reply_to(message, help_text)


@bot.message_handler(func=message_filter)
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


def notify_admin(message):
    if settings.ADMIN_CHAT_ID and message:
        bot.send_message(settings.ADMIN_CHAT_ID, message)
    logger.info(message)


if __name__ == '__main__':
    notify_admin('starting the bot')
    bot.polling(none_stop=True)
