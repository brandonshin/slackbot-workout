#!/bin/bash

if [[ $# -ne 2 ]]; then
    print "usage: $0 <ENV> <start|stop>\nwhere <ENV> is one of dev, prod"
fi

IMAGE_NAME=yucht/flexbot
LOG_FILE=slackbot.log
case $1 in
  dev)
    CONTAINER_NAME=flexbot_dev
    TAG=test
    CONFIG_FILE="$(pwd)/test-config.yaml"
    LOGGING_CONFIG_FILE="$(pwd)/log_stdout.yaml"
    PORT=8080
    ;;
  prod)
    CONTAINER_NAME=flexbot_prod
    TAG=latest
    CONFIG_FILE="$(pwd)/config.yaml"
    LOGGING_CONFIG_FILE="$(pwd)/logging.yaml"
    PORT=80
    ;;
  *)
    print "$1 is not one of dev, prod"
    exit 1;
esac

IMAGE_TO_PULL="$IMAGE_NAME:$TAG"

case $2 in
  start)
    docker pull $IMAGE_TO_PULL
    docker run -v $CONFIG_FILE:/flexbot/configuration/config.yaml -v $LOGGING_CONFIG_FILE:/flexbot/configuration/logging.yaml -v $LOG_FILE:/databricks/logs/slackbot.log -p $PORT:$PORT -d --name=$CONTAINER_NAME -t $IMAGE_TO_PULL
    ;;
  stop)
    docker stop $CONTAINER_NAME
    sleep 5
    docker rm -f $CONTAINER_NAME
    ;;
  *)
    print "$2 must be one of start, stop"
    exit 2
esac
