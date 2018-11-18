from markov import makedb
from unittest import mock


@mock.patch('markov.makedb.create_database')
@mock.patch('markov.makedb.database_exists')
@mock.patch('markov.makedb.create_engine')
@mock.patch('markov.makedb.argparse')
@mock.patch('markov.makedb.logging')
def test_create_db(
    mock_logging, mock_argparse, mock_create_engine,
    mock_database_exists, mock_create_database
):
    logger = mock.Mock()
    mock_logging.getLogger.return_value = logger

    args = mock.Mock()
    args.url = 'sqlite:///test_create_db.db'
    arg_parser = mock.Mock()
    arg_parser.parse_args.return_value = args
    mock_argparse.ArgumentParser.return_value = arg_parser

    engine = mock.Mock()
    engine.url = {'manager': 'sqlite', 'database_name': 'test_create_db.db'}
    mock_create_engine.return_value = engine

    mock_database_exists.return_value = False

    makedb.create_db()
    assert arg_parser.parse_args.called
    assert mock_create_engine.called_once_with(args.url)
    assert mock_database_exists.called_once_with(engine.url)
    assert mock_create_database.called_once_with(engine.url)


@mock.patch('markov.makedb.create_database')
@mock.patch('markov.makedb.database_exists')
@mock.patch('markov.makedb.create_engine')
@mock.patch('markov.makedb.argparse')
@mock.patch('markov.makedb.logging')
def test_create_db_already_exists(
    mock_logging, mock_argparse, mock_create_engine,
    mock_database_exists, mock_create_database
):
    logger = mock.Mock()
    mock_logging.getLogger.return_value = logger

    args = mock.Mock()
    args.url = 'sqlite:///test_create_db.db'
    arg_parser = mock.Mock()
    arg_parser.parse_args.return_value = args
    mock_argparse.ArgumentParser.return_value = arg_parser

    engine = mock.Mock()
    engine.url = {'manager': 'sqlite', 'database_name': 'test_create_db.db'}
    mock_create_engine.return_value = engine

    mock_database_exists.return_value = True

    makedb.create_db()
    assert arg_parser.parse_args.called
    assert mock_create_engine.called_once_with(args.url)
    assert mock_database_exists.called_once_with(engine.url)
    assert not mock_create_database.called
    assert logger.info.called_with('database already exists')
