import speech
from unittest import mock


@mock.patch.dict(speech.nlp, {})
@mock.patch('speech.settings')
def test_process_text(mock_settings, message):
    mock_settings.MODEL_LANG = ''
    doc = mock.Mock()
    doc._.language_scores = {'en': 0.87}
    speech.nlp['en'] = lambda t: doc
    assert speech.process_text(message.text)


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


@mock.patch('speech.process_text')
def test_PosifiedText_values(
    mock_process_text, nlp_output, parsed_sentences, message
):
    mock_process_text.return_value = nlp_output
    model = speech.PosifiedText(message.text)
    assert model.parsed_sentences == parsed_sentences
    assert model.rejoined_text == message.text


@mock.patch('speech.settings')
def test_new_model(mock_settings, message):
    mock_settings.MODEL_LANG = ''
    model = speech.new_model(message.text)
    assert isinstance(model, speech.markovify.NewlineText)


@mock.patch('speech.process_text')
@mock.patch('speech.settings')
def test_new_model_with_nlp(
    mock_settings, mock_process_text, nlp_output, message
):
    mock_settings.MODEL_LANG = ['en']
    mock_process_text.return_value = nlp_output
    model = speech.new_model(message.text)
    assert isinstance(model, speech.PosifiedText)


@mock.patch('speech.db')
def test_get_model(mock_db, one_found, message):
    mock_db.find_one.return_value = one_found
    model = speech.get_model(message.chat)
    assert mock_db.find_one.called
    assert isinstance(model, speech.PosifiedText)


@mock.patch('speech.db')
@mock.patch('speech.settings')
def test_update_model(mock_settings, mock_db, one_found, message):
    mock_settings.MODEL_LANG = ''
    mock_db.find_one.return_value = one_found
    expected_text = '\n'.join([one_found.get('text'), message.text])
    expected_chain = (
        '"[[[\\"___BEGIN__\\", \\"___BEGIN__\\"], {\\"Hello,\\": 1, '
        '\\"bla\\": 1}], [[\\"___BEGIN__\\", \\"Hello,\\"], '
        '{\\"world!\\": 1}], [[\\"Hello,\\", \\"world!\\"], '
        '{\\"___END__\\": 1}], [[\\"___BEGIN__\\", \\"bla\\"], '
        '{\\"bla\\": 1}], [[\\"bla\\", \\"bla\\"], {\\"bla\\": 1, '
        '\\"___END__\\": 1}]]"'
    )
    speech.update_model(message.chat, message.text)
    assert mock_db.find_one.called
    assert mock_db.upsert.called_once_with({
        'chat_id': message.chat.id,
        'text': expected_text,
        'chain': expected_chain
    }, ['chat_id'])


@mock.patch('speech.get_model')
@mock.patch('speech.db')
def test_delete_model(mock_db, mock_get_model, message):
    speech.delete_model(message.chat)
    assert mock_db.delete.called_once_with(chat_id=message.chat.id)
    assert mock_get_model.cache_clear.called


@mock.patch('speech.get_model')
def test_flush(mock_get_model):
    speech.flush()
    assert mock_get_model.cache_clear.called


@mock.patch('speech.get_model')
def test_new_message(mock_get_model, message):
    model = mock.Mock()
    model.make_sentence.return_value = 'Live long and prosper.'
    mock_get_model.return_value = model
    speech.new_message(message.chat)
    assert mock_get_model.called
    assert model.make_sentence.called
