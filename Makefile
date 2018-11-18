.PHONY: run test db

db:
	pipenv run python markov/makedb.py
	pipenv run alembic upgrade head

run:
	pipenv run python -m markov.markov

test:
	pipenv run pytest -v -x -p no:warnings --cov=./
