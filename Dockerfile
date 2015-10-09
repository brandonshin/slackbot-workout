FROM python:2.7.10

MAINTAINER Alex Kellen Olson <ako@byu.edu>

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python slackbotExercise.py"]
