.PHONY: run test db

migrate:
	pipenv run alembic upgrade head

db:
	pipenv run python -m markov.makedb

run:
	pipenv run python -m markov.markov

test:
	pipenv run pytest -v -x -p no:warnings --cov=./
