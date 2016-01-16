FROM ubuntu:15.04

RUN apt-get update && apt-get install -y \
    python-pip \
    postgresql-common \
    libpq-dev \
    python-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir /flexbot
COPY requirements.txt /flexbot
RUN pip install -r /flexbot/requirements.txt

FROM yucht/flexbot_base:latest

COPY . /flexbot
WORKDIR /flexbot

EXPOSE 80
EXPOSE 8080

CMD ["python", "-m", "samples.run_flexbot", "--config", "samples/config.yaml", "--logging-config", "logging.yaml"]

