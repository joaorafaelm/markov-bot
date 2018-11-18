import argparse
import logging
from markov.settings import settings
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database


def create_db():
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument('--url', '-u', help='database url')
    args = parser.parse_args()

    url = args.url if args.url else settings.DATABASE_URL
    engine = create_engine(url)

    if not database_exists(engine.url):
        logger.info('creating database')
        create_database(engine.url)
    else:
        logger.info('database already exists')


if __name__ == '__main__':
    create_db()
