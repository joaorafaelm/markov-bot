import pytest
import markov
from unittest import mock
from attrdict import AttrDict


@pytest.fixture
def message():
    AttrDict.__hash__ = lambda x: 1
    return AttrDict({
        'chat': {
            'id': -1,
            'title': 'test chat',
            'type': 'group'
        },
        'from_user': {'username': 'joao'},
        'user': {'username': 'joao'},
        'text': 'bla bla bla'
    })


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
def test_remove_messages(mock_db, mock_bot, mock_model, message):
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
def test_remove_messages_invalid(mock_db, mock_bot, mock_model, message):
    mock_bot.get_chat_administrators.return_value = []
    markov.remove_messages(message)
    assert mock_db.delete.called is False
    assert mock_model.cache_clear.called is False
    assert mock_bot.reply_to.called_once_with(message, 'u r not an admin 🤔')


@mock.patch('markov.get_model')
@mock.patch('markov.bot')
def test_flush_cache(mock_bot, mock_model, message):
    mock_bot.get_chat_administrators.return_value = [message]
    markov.flush_cache(message)
    assert mock_model.cache_clear.called
    assert mock_bot.reply_to.called


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
