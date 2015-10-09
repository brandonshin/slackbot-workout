FROM python:2.7.10-onbuild
MAINTAINER Robert Ross <robert@creativequeries.com>

CMD ["python", "./slackbotExercise.py"]

RUN mkdir -p /slackbot

# A small protection against building a container with credentials inside of it
# Just remove the config if it gets added to the container.
RUN rm ./config.json || true
