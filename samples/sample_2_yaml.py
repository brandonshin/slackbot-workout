import logging
import logging.config
import yaml

from slackbot_workout.loggers import StdOutLogger
from slackbot_workout.configurators import InMemoryTokenProvider, YamlFileConfigurationProvider
from slackbot_workout.server import Server

import os

def main():
    with open('../logging.yaml', 'r') as f:
        logging.config.dictConfig(yaml.load(f))
    logger = StdOutLogger()
    config = YamlFileConfigurationProvider(os.getcwd() + '/config.yaml')
    tokens = InMemoryTokenProvider('xoxp-2499669547-10707224704-15892141524-4b7e5a03b7')
    server = Server(logger, config, tokens)
    server.start()

if __name__ == "__main__":
    main()
