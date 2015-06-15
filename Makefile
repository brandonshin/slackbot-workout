install:
	virtualenv env
	env/bin/pip install -r requirements.txt

run: install
	env/bin/python slackbotExercise.py
