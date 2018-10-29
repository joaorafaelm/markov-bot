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


@pytest.fixture
def one_found():
    return {
        'chat_id': -1,
        'text': 'Hello, world!',
        'chain': (
            '"[[[\\"___BEGIN__\\", \\"___BEGIN__\\"], {\\"Hello,\\": 1}], '
            '[[\\"___BEGIN__\\", \\"Hello,\\"], {\\"world!\\": 1}], '
            '[[\\"Hello,\\", \\"world!\\"], {\\"___END__\\": 1}]]"'
        )
    }


@pytest.fixture
def nlp_output():
    AttrDict.__hash__ = lambda x: 2
    return [
        AttrDict({'text': 'bla', 'pos_': 'X', 'dep_': 'compound'}),
        AttrDict({'text': 'bla', 'pos_': 'X', 'dep_': 'compound'}),
        AttrDict({'text': 'bla', 'pos_': 'NOUN', 'dep_': 'ROOT'})
    ]


@pytest.fixture
def parsed_sentences():
    return [['bla::X::compound', 'bla::X::compound', 'bla::NOUN::ROOT']]
