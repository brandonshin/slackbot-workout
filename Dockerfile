FROM ubuntu:15.04

EXPOSE 80

RUN apt-get update && apt-get install -y \
    python-pip \
    postgresql-common \
    libpq-dev \
    python-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir /flexbot /flexbot/configuration /flexbot/flexbot /flexbot/samples

COPY requirements.txt /flexbot
RUN pip install -r /flexbot/requirements.txt

COPY flexbot /flexbot/flexbot
COPY samples /flexbot/samples

WORKDIR /flexbot
CMD ["python", "-m", "samples.run_flexbot", "--config", "configuration/config.yaml", "--logging-config", "configuration/logging.yaml"]

