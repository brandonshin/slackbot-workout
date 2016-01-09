import logging
import logging.config
import yaml

from slackbot_workout.configurators import YamlFileConfigurationProvider
from slackbot_workout.server import Server

import os

def main():
    with open('logging.yaml', 'r') as f:
        logging.config.dictConfig(yaml.load(f))
    config = YamlFileConfigurationProvider(os.getcwd() + '/config.yaml')
    server = Server(config)
    server.start()

if __name__ == "__main__":
    main()
