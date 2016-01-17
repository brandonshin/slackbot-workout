import logging
import logging.config
import yaml

from flexbot.configurators import YamlFileConfigurationProvider
from flexbot.server import Server

import os

def main():
    with open('logging.yaml', 'r') as f:
        logging.config.dictConfig(yaml.load(f))
    config = YamlFileConfigurationProvider(os.getcwd() + '/config.yaml')
    server = Server(config)
    server.start()

if __name__ == "__main__":
    main()
