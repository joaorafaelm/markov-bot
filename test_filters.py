import filters
from unittest import mock


@mock.patch('filters.filters', [r'^hello'])
def test_message_filter(message):
    assert filters.message_filter(message) is True
    message.text = 'Hello, World'
    assert filters.message_filter(message) is False
