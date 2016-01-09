import logging
import logging.config
import os

from slackbot_workout.loggers import StdOutLogger
from slackbot_workout.configurators import JsonFileConfigurationProvider
from slackbot_workout.server import Server

def main():
    logging.config.fileConfig('logging.conf')
    logger = StdOutLogger()
    config = JsonFileConfigurationProvider(os.getcwd() + '/config.json')
    server = Server(logger, config)
    server.start()

if __name__ == "__main__":
    main()
