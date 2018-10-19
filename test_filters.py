import pytest
import filters
from unittest import mock
from attrdict import AttrDict


@pytest.fixture
def message():
    return AttrDict({
        'chat': {
            'id': -1,
            'title': 'test filters',
            'type': 'group'
        },
        'from_user': {'username': 'peter'},
        'user': {'username': 'peter'},
        'text': 'Peter Piper picked a peck of pickled peppers'
    })


@mock.patch('filters.filters', [r'^hello'])
def test_message_filter(message):
    assert filters.message_filter(message) is True
    message.text = 'Hello, World'
    assert filters.message_filter(message) is False
