from markov import markov
from unittest import mock


@mock.patch('markov.markov.generate_sentence')
@mock.patch('markov.speech.update_model')
@mock.patch('markov.markov.bot')
def test_handle_message(
    mock_bot, mock_update_model, mock_generate_sentence, message
):
    mock_get_me = mock.Mock()
    mock_get_me.return_value.username = 'markov_bot'
    mock_bot.get_me = mock_get_me

    markov.handle_message(message)
    assert mock_update_model.called
    assert not mock_generate_sentence.called


@mock.patch('markov.markov.generate_sentence')
@mock.patch('markov.speech.update_model')
@mock.patch('markov.markov.bot')
def test_handle_message_with_mention(
    mock_bot, mock_update_model, mock_generate_sentence, message
):
    message.text = 'hello, @markov_bot!'
    mock_get_me = mock.Mock()
    mock_get_me.return_value.username = 'markov_bot'
    mock_bot.get_me = mock_get_me

    markov.handle_message(message)
    assert mock_update_model.called
    assert mock_generate_sentence.called


@mock.patch('markov.markov.generate_sentence')
@mock.patch('markov.speech.update_model')
@mock.patch('markov.markov.bot')
def test_handle_message_raising_exception(
    mock_bot, mock_update_model, mock_generate_sentence, message
):
    mock_update_model.side_effect = ValueError('invalid param')
    message.text = ''
    markov.handle_message(message)
    assert not mock_bot.get_me.called
    assert not mock_generate_sentence.called


@mock.patch('markov.speech.new_message')
@mock.patch('markov.markov.bot')
def test_generate_sentence(mock_bot, mock_new_message, message):
    markov.generate_sentence(message)
    assert mock_new_message.called
    assert not mock_bot.reply_to.called
    assert mock_bot.send_message.called


@mock.patch('markov.speech.new_message')
@mock.patch('markov.markov.bot')
def test_generate_sentence_for_reply(mock_bot, mock_new_message, message):
    markov.generate_sentence(message, reply=True)
    assert mock_new_message.called
    assert mock_bot.reply_to.called
    assert not mock_bot.send_message.called


@mock.patch('markov.speech.delete_model')
@mock.patch('markov.markov.bot')
def test_remove_messages_no_permission(mock_bot, mock_delete_model, message):
    mock_bot.get_chat_administrators.return_value = []
    markov.remove_messages(message)
    assert mock_bot.reply_to.called_once_with(message, 'u r not an admin 🤔')
    assert not mock_delete_model.delete.called


@mock.patch('markov.markov.telebot.types.ReplyKeyboardMarkup')
@mock.patch('markov.speech.delete_model')
@mock.patch('markov.markov.bot')
def test_remove_messages_ask_confirm(
    mock_bot, mock_delete_model, mock_markup, message
):
    message.text = '/remove'
    mock_bot.get_chat_administrators.return_value = [message]
    markov.remove_messages(message)
    assert mock_markup.add.called_once_with('yes', 'no')
    assert mock_bot.reply_to.called_once_with(
        message, 'are you sure?', reply_markup=mock_markup)
    assert mock_bot.register_next_step_handler.called
    assert not mock_delete_model.called


@mock.patch('markov.markov.telebot.types.ReplyKeyboardRemove')
@mock.patch('markov.speech.delete_model')
@mock.patch('markov.markov.bot')
def test_remove_messages_confirm(
    mock_bot, mock_delete_model, mock_markup, message
):
    message.text = 'yes'
    mock_bot.get_chat_administrators.return_value = [message]
    markov.remove_messages(message)
    assert mock_delete_model.called
    assert mock_bot.reply_to.called_once_with(
        message, 'okay', reply_markup=mock_markup)


@mock.patch('markov.markov.telebot.types.ReplyKeyboardRemove')
@mock.patch('markov.speech.delete_model')
@mock.patch('markov.markov.bot')
def test_remove_messages_cancel(
    mock_bot, mock_delete_model, mock_markup, message
):
    message.text = 'no'
    mock_bot.get_chat_administrators.return_value = [message]
    markov.remove_messages(message)
    assert mock_bot.reply_to.called_once_with(
        message, 'okay', reply_markup=mock_markup)
    assert not mock_delete_model.called


@mock.patch('markov.speech.flush')
@mock.patch('markov.markov.bot')
def test_flush_cache_no_permission(mock_bot, mock_flush, message):
    mock_bot.get_chat_administrators.return_value = []
    markov.flush_cache(message)
    assert mock_bot.reply_to.called_once_with(message, 'u r not an admin 🤔')
    assert not mock_flush.called


@mock.patch('markov.markov.telebot.types.ReplyKeyboardMarkup')
@mock.patch('markov.speech.flush')
@mock.patch('markov.markov.bot')
def test_flush_cache_ask_confirm(
    mock_bot, mock_flush, mock_markup, message
):
    message.text = '/flush'
    mock_bot.get_chat_administrators.return_value = [message]
    markov.flush_cache(message)
    assert mock_markup.add.called_once_with('yes', 'no')
    assert mock_bot.reply_to.called_once_with(
        message, 'are you sure?', reply_markup=mock_markup)
    assert mock_bot.register_next_step_handler.called
    assert not mock_flush.called


@mock.patch('markov.markov.telebot.types.ReplyKeyboardRemove')
@mock.patch('markov.speech.flush')
@mock.patch('markov.markov.bot')
def test_flush_cache_confirm(mock_bot, mock_flush, mock_markup, message):
    message.text = 'yes'
    mock_bot.get_chat_administrators.return_value = [message]
    markov.flush_cache(message)
    assert mock_flush.called
    assert mock_bot.reply_to.called_once_with(
        message, 'okay', reply_markup=mock_markup)


@mock.patch('markov.markov.telebot.types.ReplyKeyboardRemove')
@mock.patch('markov.speech.flush')
@mock.patch('markov.markov.bot')
def test_flush_cache_cancel(mock_bot, mock_flush, mock_markup, message):
    message.text = 'no'
    mock_bot.get_chat_administrators.return_value = [message]
    markov.flush_cache(message)
    assert mock_bot.reply_to.called_once_with(
        message, 'okay', reply_markup=mock_markup)
    assert not mock_flush.called


@mock.patch('markov.markov.bot')
def test_get_repo_version(mock_bot, message):
    markov.get_repo_version(message)
    assert mock_bot.reply_to.called


@mock.patch('markov.markov.bot')
@mock.patch('markov.markov.settings')
def test_notify_admin(mock_settings, mock_bot):
    mock_settings.ADMIN_CHAT_ID = 'ae'
    message = 'ae'
    markov.notify_admin(message)
    assert mock_bot.send_message.called_once_with(
        mock_settings.ADMIN_CHAT_ID,
        message
    )


@mock.patch('markov.markov.bot')
def test_help(mock_bot, message):
    markov.help(message)
    assert mock_bot.reply_to.called


@mock.patch('markov.markov.bot')
def test_start(mock_bot, message):
    markov.start(message)
    assert mock_bot.reply_to.called
