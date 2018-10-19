import pytest
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
