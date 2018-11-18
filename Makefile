.PHONY: run test db

db:
	pipenv run python makedb.py
	pipenv run alembic upgrade head

run:
	pipenv run python markov.py

test:
	pipenv run pytest -v -x -p no:warnings --cov=./
