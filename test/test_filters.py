from markov import filters
from unittest import mock


@mock.patch('markov.filters.filters', [r'^hello'])
def test_message_filter(message):
    assert filters.message_filter(message)
    message.text = 'Hello, World'
    assert not filters.message_filter(message)


def test_empty_message(message):
    message.text = None
    assert not filters.message_filter(message)
