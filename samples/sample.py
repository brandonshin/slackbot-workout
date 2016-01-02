import os

from slackbot_workout.configurators import EnvironmentTokenProvider, JsonFileConfigurationProvider
from slackbot_workout.loggers import StdOutLogger
from slackbot_workout.server import Server

def main():
    logger = StdOutLogger()
    config = JsonFileConfigurationProvider(os.getcwd() + '/config.json')
    tokens = EnvironmentTokenProvider()
    server = Server(logger, config, tokens)
    server.start()

if __name__ == "__main__":
    main()
