import telebot
import markovify
from os import environ
from os.path import isfile
import pickle


models = pickle.load(
    open('models.pkl', 'rb')
) if isfile('models.pkl') else {}


telegram_token = environ.get('TELEGRAM_TOKEN')
admin_usernames = environ.get('ADMIN_USERNAMES', '').split(',')
sentence_command = environ.get('SENTENCE_COMMAND', 'sentence')
bot = telebot.TeleBot(telegram_token)

print('Token: {}'.format(telegram_token))
print('Admins: {}'.format(admin_usernames))


def update_model(chat_name):
    text_file = 'data/{}.txt'.format(chat_name)
    if isfile(text_file):
        models[chat_name] = markovify.text.NewlineText(
            open(text_file).read()
        )
        pickle.dump(models, open('models.pkl', 'wb'))


@bot.message_handler(commands=[sentence_command])
def sentence(message):
    chat_title = message.chat.title
    chat_model = models.get(chat_title)
    if chat_model and chat_title in models:
        generated_message = chat_model.make_sentence(
            max_overlap_ratio=0.7,
            tries=50
        )

        bot.send_message(
            message.chat.id,
            generated_message or 'i need more data'
        )
        return

    bot.reply_to(message, 'enable the chat first')


@bot.message_handler(commands=['enable', 'remove'])
def admin(message):
    username = message.from_user.username
    chat_title = message.chat.title

    if username not in admin_usernames:
        bot.reply_to(message, 'u r not an admin 🤔')
        return

    if 'remove' in message.text and chat_title in models:
        models.pop(chat_title)
    elif 'enable' in message.text:
        models[chat_title] = None
        update_model(chat_title)

    bot.reply_to(message, 'chat config updated')
    pickle.dump(models, open('models.pkl', 'wb'))


@bot.message_handler(func=lambda m: True)
def messages(message):
    chat_title = message.chat.title
    text_file = 'data/{}.txt'.format(chat_title)
    if chat_title in models:
        with open(text_file, 'a+') as f:
            f.write(message.text + '\n')
        update_model(chat_title)


bot.polling(none_stop=True)
