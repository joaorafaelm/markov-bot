import re
import json
import spacy
import dataset
import logging
import operator
import markovify
from attrdict import AttrDict
from markov.settings import settings
from cachetools.func import ttl_cache
from spacy_cld import LanguageDetector

logger = logging.getLogger(__name__)

# ignore thread checking for sqlite
engine_config = {
    'connect_args': {'check_same_thread': False}
} if settings.DATABASE_URL.startswith('sqlite') else {}

db = dataset.connect(
    settings.DATABASE_URL, engine_kwargs=engine_config
)['messages']


def load_nlp_models(languages=[]):
    nlp_models = None
    if languages:
        nlp_models = AttrDict({'languages': [], 'processors': []})
        ld = LanguageDetector()
        for lang in languages:
            try:
                model = spacy.load(lang)
            except OSError:
                logger.error(f'{lang} spacy module not found')
                continue
            model.add_pipe(ld)
            nlp_models['languages'].append(lang)
            nlp_models['processors'].append((lang, model))
        if not nlp_models['languages']:
            nlp_models = None
    return nlp_models


nlp = load_nlp_models(settings.MODEL_LANG)


def process_text(text):
    logger.debug('performing n.l.p.')
    if not nlp:
        return text
    lang, proc = nlp.processors[0]
    doc = proc(text)
    scores = doc._.language_scores.items()
    if scores:
        guess = max(scores, key=operator.itemgetter(1))[0]
        if guess != lang and guess in nlp.languages:
            lang, proc = nlp.processors[nlp.languages.index(guess)]
            doc = proc(text)
    return doc


class PosifiedText(markovify.NewlineText):
    def word_split(self, sentence):
        logger.debug('spliting sentece into words')
        return ['::'.join((w.text, w.pos_, w.dep_))
                for w in process_text(sentence)]

    def word_join(self, words):
        logger.debug('joining words into sentence')
        sentence = ' '.join(w.split('::')[0] for w in words)
        return re.sub(r'\s([!?.,;"](?:\s|$))', r'\1', sentence)


def new_model(text):
    logger.debug('creating a new model')
    Cls = PosifiedText if settings.MODEL_LANG else markovify.NewlineText
    model = None
    try:
        model = Cls(re.sub(r'["\']', '', text),
                    retain_original=settings.RETAIN_ORIG)
    except KeyError:
        logger.error(f'cannot create a chain from {text}')
    return model


@ttl_cache(ttl=settings.MODEL_CACHE_TTL)
def get_model(chat):
    logger.debug(f'fetching model for chat-id:{chat.id}')
    chat_id = str(chat.id)
    chat_data = db.find_one(chat_id=chat_id) or {}
    if chat_data.get('chain', ''):
        Cls = PosifiedText if settings.MODEL_LANG else markovify.NewlineText
        chain = json.loads(chat_data.get('chain'))
        return Cls.from_chain(chain, corpus=chat_data.get('text', ''))


def update_model(chat, message):
    if not chat or not hasattr(chat, 'id'):
        raise ValueError('invalid type for chat')
    if not message:
        raise ValueError('message cannot be empty')
    logger.debug(f'updating model for chat-id:{chat.id}')
    model = new_model(message)
    if not model:
        return
    else:
        model = model.chain
    chat_id = str(chat.id)
    chat_data = db.find_one(chat_id=chat_id) or {}
    text = '\n'.join([chat_data.get('text', ''), message])
    if chat_data.get('chain', ''):
        if settings.GROW_CHAIN:
            chain = json.loads(chat_data.get('chain'))
            cur_m = markovify.Chain.from_json(chain)
            model = markovify.combine([cur_m, model])
        else:
            text = '\n'.join(
                text.splitlines()[-settings.MESSAGE_LIMIT:])
            model = new_model(text).chain
    db.upsert({
        'chat_id': chat_id,
        'text': text,
        'chain': json.dumps(model.to_json())
    }, ['chat_id'])


def delete_model(chat):
    logger.debug(f'deleting model for chat-id:{chat.id}')
    chat_id = str(chat.id)
    db.delete(chat_id=chat_id)
    get_model.cache_clear()


def flush():
    logger.debug('cleaning up models\' cache')
    get_model.cache_clear()


def new_message(chat):
    logger.debug(f'generating message for chat-id:{chat.id}')
    model = get_model(chat)
    message = None
    if model:
        message = model.make_sentence(
            max_overlap_ratio=settings.MAX_OVERLAP_RATIO,
            tries=settings.TRIES
        )

    return message or 'i need more data'
