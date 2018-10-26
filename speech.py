import re
import json
import spacy
import dataset
import logging
import operator
import markovify
from settings import settings
from cachetools.func import ttl_cache
from spacy_cld import LanguageDetector

logger = logging.getLogger(__name__)
db = dataset.connect(settings.DATABASE_URL)[settings.MESSAGES_TABLE_NAME]

if settings.MODEL_LANG:
    ld = LanguageDetector()
    nlp = {}
    for lang in settings.MODEL_LANG:
        nlp[lang] = spacy.load(lang)
        nlp[lang].add_pipe(ld)


class PosifiedText(markovify.NewlineText):
    def word_split(self, sentence):
        logger.debug('spliting sentece into words')
        return ['::'.join((w.text, w.pos_, w.dep_))
                for w in self.nlp(sentence)]

    def word_join(self, words):
        logger.debug('joining words into sentence')
        sentence = ' '.join(w.split('::')[0] for w in words)
        return re.sub(r'\s([!?.,;"](?:\s|$))', r'\1', sentence)

    def nlp(self, text):
        logger.debug('performing n.l.p.')
        lang = next(iter(nlp))
        doc = nlp[lang](text)
        scores = doc._.language_scores.items()
        if scores:
            guess = max(scores, key=operator.itemgetter(1))[0]
            if guess != lang and guess in nlp:
                doc = nlp[guess](text)
        return doc


def new_model(text):
    Cls = PosifiedText if settings.MODEL_LANG else markovify.NewlineText
    return Cls(text, retain_original=False)


@ttl_cache(ttl=settings.MODEL_CACHE_TTL)
def get_model(chat):
    logger.debug(f'fetching model for chat-id:{chat.id}')
    chat_data = db.find_one(chat_id=chat.id) or {}
    if chat_data.get('chain', ''):
        chain = json.loads(chat_data.get('chain'))
        return PosifiedText.from_chain(chain)


def update_model(chat, message):
    logger.debug(f'updating model for chat-id:{chat.id}')
    model = new_model(message).chain
    chat_data = db.find_one(chat_id=chat.id) or {}
    if chat_data.get('chain', ''):
        chain = json.loads(chat_data.get('chain'))
        cur_m = markovify.Chain.from_json(chain)
        model = markovify.combine([cur_m, model])
    db.upsert({
        'chat_id': chat.id,
        'text': '\n'.join([chat_data.get('text', ''), message]),
        'chain': json.dumps(model.to_json())
    }, ['chat_id'])


def delete_model(chat):
    logger.debug(f'deleting model for chat-id:{chat.id}')
    db.delete(chat_id=chat.id)
    get_model.cache_clear()


def flush():
    logger.debug('cleaning up models\' cache')
    get_model.cache_clear()


def new_message(chat):
    logger.debug(f'generating message for chat-id:{chat.id}')
    model = get_model(chat)
    if model:
        return model.make_sentence(tries=50)
    else:
        return 'i need more data'
