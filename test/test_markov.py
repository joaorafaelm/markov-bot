import markov
from unittest import mock


@mock.patch('markov.generate_sentence')
@mock.patch('markov.update_model')
@mock.patch('markov.bot')
@mock.patch('markov.db')
def test_handle_message(
    mock_db, mock_bot, mock_update_model,
    mock_generate_sentence, message
):
    mock_get_me = mock.Mock()
    mock_get_me.return_value.username = 'markov_bot'
    mock_bot.get_me = mock_get_me

    markov.handle_message(message)
    assert mock_update_model.called
    assert not mock_generate_sentence.called


@mock.patch('markov.update_model')
@mock.patch('markov.bot')
@mock.patch('markov.db')
def test_handle_message_with_mention(
    mock_db, mock_bot, mock_update_model,
    message
):
    mock_db.find_one.return_value = {'text': 'bla bla bla'}
    message.text = 'hello, @markov_bot!'

    mock_get_me = mock.Mock()
    mock_get_me.return_value.username = 'markov_bot'
    mock_bot.get_me = mock_get_me

    markov.handle_message(message)
    assert mock_update_model.called
    assert mock_bot.reply_to.called


@mock.patch('markov.bot')
@mock.patch('markov.db')
def test_update_model(mock_db, mock_bot, message):
    mock_db.find_one.return_value = ''
    chat_id = str(message.chat.id)
    markov.update_model(message)
    assert mock_db.find_one.called_once_with(chat_id=chat_id)
    assert mock_db.upsert.called_once_with({
        'chat_id': chat_id,
        'text': f'\n{message.text}'
    }, ['chat_id'])


@mock.patch('markov.db')
def test_get_model(mock_db, message):
    mock_db.find_one.return_value = {'text': 'bla bla bla'}
    model = markov.get_model(message.chat)
    chat_id = str(message.chat.id)
    assert mock_db.find_one.called_once_with(chat_id=chat_id)
    assert model is not None


@mock.patch('markov.bot')
@mock.patch('markov.get_model')
def test_generate_sentence(mock_model, mock_bot, message):
    markov.generate_sentence(message)
    assert mock_model.called_once_with(message.chat)
    assert mock_bot.send_message.called is True


@mock.patch('markov.get_model')
@mock.patch('markov.bot')
@mock.patch('markov.db')
@mock.patch('markov.telebot.types.ReplyKeyboardMarkup')
def test_remove_messages_ask_confirm(
    mock_markup, mock_db, mock_bot, mock_model, message
):
    message.text = '/remove'
    mock_bot.get_chat_administrators.return_value = [message]
    markov.remove_messages(message)
    assert mock_markup.add.called_once_with('yes', 'no')
    assert mock_bot.reply_to.called_once_with(
        message,
        'this operation will delete all data, are you sure?',
        reply_markup=mock_markup
    )
    assert mock_bot.register_next_step_handler.called is True


@mock.patch('markov.get_model')
@mock.patch('markov.bot')
@mock.patch('markov.db')
def test_remove_messages_confirm(mock_db, mock_bot, mock_model, message):
    message.text = 'yes'
    mock_bot.get_chat_administrators.return_value = [message]
    chat_id = str(message.chat.id)
    markov.remove_messages(message)
    assert mock_db.delete.called_once_with(chat_id=chat_id)
    assert mock_model.cache_clear.called
    assert mock_bot.reply_to.called


@mock.patch('markov.get_model')
@mock.patch('markov.bot')
@mock.patch('markov.db')
def test_remove_messages_cancel(mock_db, mock_bot, mock_model, message):
    message.text = 'no'
    mock_bot.get_chat_administrators.return_value = [message]
    markov.remove_messages(message)
    assert mock_db.delete.called is False
    assert mock_model.cache_clear.called is False


@mock.patch('markov.get_model')
@mock.patch('markov.bot')
@mock.patch('markov.db')
def test_remove_messages_no_permission(mock_db, mock_bot, mock_model, message):
    mock_bot.get_chat_administrators.return_value = []
    markov.remove_messages(message)
    assert mock_db.delete.called is False
    assert mock_model.cache_clear.called is False
    assert mock_bot.reply_to.called_once_with(message, 'u r not an admin 🤔')


@mock.patch('markov.get_model')
@mock.patch('markov.bot')
def test_flush_cache(mock_bot, mock_model, message):
    message.text = 'yes'
    mock_bot.get_chat_administrators.return_value = [message]
    markov.flush_cache(message)
    assert mock_model.cache_clear.called


@mock.patch('markov.get_model')
@mock.patch('markov.bot')
def test_flush_cache_invalid(mock_bot, mock_model, message):
    mock_bot.get_chat_administrators.return_value = []
    markov.flush_cache(message)
    assert mock_model.cache_clear.called is False
    assert mock_bot.reply_to.called_once_with(message, 'u r not an admin 🤔')


@mock.patch('markov.bot')
def test_get_repo_version(mock_bot, message):
    markov.get_repo_version(message)
    assert mock_bot.reply_to.mock_model.called_once_with(message)


@mock.patch('markov.bot')
@mock.patch('markov.settings')
def test_notify_admin(mock_settings, mock_bot):
    mock_settings.ADMIN_CHAT_ID = 'ae'
    message = 'ae'
    markov.notify_admin(message)
    assert mock_bot.send_message.called_once_with(
        mock_settings.ADMIN_CHAT_ID,
        message
    )


@mock.patch('markov.bot')
def test_help(mock_bot, message):
    markov.help(message)
    assert mock_bot.reply_to.called


@mock.patch('markov.bot')
def test_start(mock_bot, message):
    markov.start(message)
    assert mock_bot.reply_to.called
