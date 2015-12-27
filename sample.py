from logger.loggers import StdOutLogger
from util.configurators import EnvironmentTokenProvider, JsonFileConfigurationProvider
import os
from server.server import Server

def main():
    logger = StdOutLogger()
    config = JsonFileConfigurationProvider(os.getcwd() + '/config.json')
    tokens = EnvironmentTokenProvider()
    server = Server(logger, config, tokens)
    server.start()

if __name__ == "__main__":
    main()
