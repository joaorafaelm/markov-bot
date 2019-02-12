from markov import speech
from pytest import mark, raises
from unittest import mock
from attrdict import AttrDict


@mock.patch('markov.speech.LanguageDetector')
@mock.patch('markov.speech.spacy')
def test_load_nlp_models(mock_spacy, mock_language_detector):
    lang = 'en'
    proc = mock.Mock()
    mock_spacy.load.return_value = proc
    nlp = speech.load_nlp_models([lang])
    assert isinstance(nlp, AttrDict)
    assert 'languages' in nlp
    assert 'processors' in nlp
    assert nlp.languages == (lang,)
    assert nlp.processors == ((lang, proc),)


@mock.patch('markov.speech.LanguageDetector')
def test_load_nlp_models_invalid_lang(mock_language_detector):
    nlp = speech.load_nlp_models(['zz'])
    assert nlp is None


def test_load_nlp_models_no_lang():
    assert speech.load_nlp_models('') is None


@mock.patch('markov.speech.nlp')
def test_process_text(mock_nlp, nlp_output, message):
    doc = mock.Mock()
    doc.return_value = nlp_output
    doc._.language_scores = {'en': 0.87}
    mock_nlp.languages = ['en']
    mock_nlp.processors = [('en', lambda t: doc)]
    assert speech.process_text(message.text) == doc


@mock.patch('markov.speech.nlp')
def test_process_text_guessed_lang(mock_nlp, nlp_output, message):
    doc1 = mock.Mock()
    doc1.return_value = nlp_output
    doc1._.language_scores = {'en': 0.11, 'pt': 0.89}

    doc2 = mock.Mock()
    doc2.return_value = reversed(nlp_output)
    doc2._.language_scores = {'en': 0.11, 'pt': 0.89}

    mock_nlp.languages = ['en', 'pt']
    mock_nlp.processors = [('en', lambda t: doc1), ('pt', lambda t: doc2)]
    assert speech.process_text(message.text) == doc2


@mock.patch('markov.speech.nlp', None)
def test_process_text_without_nlp(message):
    assert speech.process_text(message.text) == message.text


@mock.patch.object(speech.PosifiedText, 'word_join')
@mock.patch.object(speech.PosifiedText, 'word_split')
def test_PosifiedText_sequence(
    mock_word_split, mock_word_join, parsed_sentences, message
):
    mock_word_join.return_value = message.text
    mock_word_split.return_value = parsed_sentences[0]
    speech.PosifiedText(message.text)
    assert mock_word_split.called
    assert mock_word_join.called


@mock.patch('markov.speech.process_text')
def test_PosifiedText_values(
    mock_process_text, nlp_output, parsed_sentences, message
):
    mock_process_text.return_value = nlp_output
    model = speech.PosifiedText(message.text)
    assert model.parsed_sentences == parsed_sentences
    assert model.rejoined_text == message.text


@mock.patch('markov.speech.settings')
def test_new_model(mock_settings, message):
    mock_settings.MODEL_LANG = ''
    model = speech.new_model(message.text)
    assert isinstance(model, speech.markovify.NewlineText)


@mock.patch('markov.speech.settings')
def test_new_model_with_invalid_msg(mock_settings, message):
    mock_settings.MODEL_LANG = ''
    message.text = '\n'
    model = speech.new_model(message.text)
    assert not model


@mock.patch('markov.speech.process_text')
@mock.patch('markov.speech.settings')
def test_new_model_with_nlp(
    mock_settings, mock_process_text, nlp_output, message
):
    mock_settings.MODEL_LANG = ['en']
    mock_process_text.return_value = nlp_output
    model = speech.new_model(message.text)
    assert isinstance(model, speech.PosifiedText)


@mock.patch('markov.speech.db')
def test_get_model(mock_db, one_found, message):
    mock_db.find_one.return_value = one_found
    model = speech.get_model(message.chat)
    assert mock_db.find_one.called
    assert isinstance(model, speech.markovify.NewlineText)


@mark.parametrize('p_grow,p_limit,expected_text,expected_chain', [
    (
        True,
        None,
        'Hello, world!\nbla bla bla',
        (
            '"[[[\\"___BEGIN__\\", \\"___BEGIN__\\"], {\\"Hello,\\": 1, '
            '\\"bla\\": 1}], [[\\"___BEGIN__\\", \\"Hello,\\"], '
            '{\\"world!\\": 1}], [[\\"Hello,\\", \\"world!\\"], '
            '{\\"___END__\\": 1}], [[\\"___BEGIN__\\", \\"bla\\"], '
            '{\\"bla\\": 1}], [[\\"bla\\", \\"bla\\"], {\\"bla\\": 1, '
            '\\"___END__\\": 1}]]"'
        )
    ),
    (
        False,
        1,
        'bla bla bla',
        (
            '"[[[\\"___BEGIN__\\", \\"___BEGIN__\\"], {\\"bla\\": 1}], '
            '[[\\"___BEGIN__\\", \\"bla\\"], {\\"bla\\": 1}], [[\\"bla\\", '
            '\\"bla\\"], {\\"bla\\": 1, \\"___END__\\": 1}]]"'
        )
    )
])
@mock.patch('markov.speech.db')
@mock.patch('markov.speech.settings')
def test_update_model(
    mock_settings, mock_db, p_grow, p_limit,
    expected_text, expected_chain, one_found, message
):
    mock_settings.MODEL_LANG = ''
    mock_settings.GROW_CHAIN = p_grow
    mock_settings.MESSAGE_LIMIT = p_limit
    mock_db.find_one.return_value = one_found
    speech.update_model(message.chat, message.text)
    assert mock_db.find_one.called
    assert mock_db.upsert.called_once_with({
        'chat_id': message.chat.id,
        'text': expected_text,
        'chain': expected_chain
    }, ['chat_id'])


@mock.patch('markov.speech.db')
@mock.patch('markov.speech.settings')
def test_update_model_with_invalid_msg(mock_settings, mock_db, message):
    mock_settings.MODEL_LANG = ''
    message.text = '\n'
    speech.update_model(message.chat, message.text)
    assert not mock_db.find_one.called
    assert not mock_db.upsert.called


@mark.parametrize('p_chat,p_message,p_expected', [
    (None, 'bla bla bla', 'invalid type for chat'),
    (AttrDict({'id': -1}), '', 'message cannot be empty')
])
def test_update_model_raises_exception(p_chat, p_message, p_expected):
    with raises(ValueError) as er:
        speech.update_model(p_chat, p_message)
    assert str(er.value) == p_expected


@mock.patch('markov.speech.get_model')
@mock.patch('markov.speech.db')
def test_delete_model(mock_db, mock_get_model, message):
    speech.delete_model(message.chat)
    assert mock_db.delete.called_once_with(chat_id=message.chat.id)
    assert mock_get_model.cache_clear.called


@mock.patch('markov.speech.get_model')
def test_flush(mock_get_model):
    speech.flush()
    assert mock_get_model.cache_clear.called


@mock.patch('markov.speech.get_model')
def test_new_message(mock_get_model, message):
    model = mock.Mock()
    model.make_sentence.return_value = 'Live long and prosper.'
    mock_get_model.return_value = model
    speech.new_message(message.chat)
    assert mock_get_model.called
    assert model.make_sentence.called


@mock.patch('markov.speech.get_model')
def test_new_message_empty_model(mock_get_model, message):
    mock_get_model.return_value = None
    msg = speech.new_message(message.chat)
    assert mock_get_model.called
    assert msg == 'i need more data'
