run:
	pipenv run python markov.py

test:
	pipenv run pytest -v -x -p no:warnings --cov=./
