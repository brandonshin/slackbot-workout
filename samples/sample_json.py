import logging
import logging.config
import os

from flexbot.configurators import JsonFileConfigurationProvider
from flexbot.server import Server

def main():
    logging.config.fileConfig('logging.conf')
    config = JsonFileConfigurationProvider(os.getcwd() + '/config.json')
    server = Server(config)
    server.start()

if __name__ == "__main__":
    main()
