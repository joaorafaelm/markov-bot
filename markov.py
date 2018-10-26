import telebot
import speech
import logging
import functools
from settings import settings
from filters import message_filter

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

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


@bot.message_handler(commands=[settings.SENTENCE_COMMAND])
def generate_sentence(message, reply=False):
    logger.info(f'sentence cmd called by chat {message.chat.id}')
    generated_message = speech.new_message(message.chat)
    if reply:
        bot.reply_to(message, generated_message)
    else:
        bot.send_message(message.chat.id, generated_message)


@bot.message_handler(commands=[settings.REMOVE_COMMAND])
@admin_required
@confirmation_required
def remove_messages(message):
    logger.info(f'remove cmd called by chat {message.chat.id}')
    speech.delete_model(message.chat)


@bot.message_handler(commands=[settings.VERSION_COMMAND])
def get_repo_version(message):
    logger.info(f'version cmd called by chat {message.chat.id}')
    hash_len = 7
    commit_hash = settings.COMMIT_HASH[:hash_len]
    bot.reply_to(message, commit_hash)


@bot.message_handler(commands=[settings.FLUSH_COMMAND])
@admin_required
@confirmation_required
def flush_cache(message):
    logger.info(f'flush cmd called by chat {message.chat.id}')
    speech.flush()


@bot.message_handler(commands=[settings.HELP_COMMAND])
def help(message):
    logger.info(f'help cmd called by chat {message.chat.id}')
    username = bot.get_me().username
    sentence_command = settings.SENTENCE_COMMAND
    remove_command = settings.REMOVE_COMMAND
    version_command = settings.VERSION_COMMAND
    flush_command = settings.FLUSH_COMMAND
    help_command = settings.HELP_COMMAND

    help_text = (
        "Welcome to MarkovBot, a Telegram bot that writes like you do using "
        "Markov chains!\n\n"
        "{sentence_command}: {username} will generate a message.\n"
        "{remove_command}: {username} will remove messages from chat.\n"
        "{version_command}: {username} will state its current version.\n"
        "{flush_command}: {username} will clear its cache.\n"
        "{help_command}: {username} will print this help message!"
    )
    output_text = help_text.format(
        username=username, sentence_command=sentence_command,
        remove_command=remove_command, version_command=version_command,
        flush_command=flush_command, help_command=help_command
    )
    bot.reply_to(message, output_text)


@bot.message_handler(func=message_filter)
def handle_message(message):
    speech.update_model(message.chat, message.text)
    if f'@{bot.get_me().username}' in message.text:
        generate_sentence(message, reply=True)


def notify_admin(message):
    if settings.ADMIN_CHAT_ID and message:
        bot.send_message(settings.ADMIN_CHAT_ID, message)
    logger.info(message)


if __name__ == '__main__':
    notify_admin('starting the bot')
    bot.polling(none_stop=True)
