from logger.loggers import StdOutLogger
from util.configurators import InMemoryTokenProvider, JsonFileConfigurationProvider
import os
from server.server import Server

def main():
    logger = StdOutLogger()
    config = JsonFileConfigurationProvider(os.getcwd() + '/config.json')
    tokens = InMemoryTokenProvider('xoxp-2499669547-10707224704-15892141524-4b7e5a03b7')
    server = Server(logger, config, tokens)
    server.start()

if __name__ == "__main__":
    main()
