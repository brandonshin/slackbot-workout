from slackbot_workout.server import Server
from slackbot_workout.loggers import PostgresDatabaseLogger
from slackbot_workout.configurators import EnvironmentTokenProvider, JsonFileConfigurationProvider
import os

def main():
    logger = PostgresDatabaseLogger('flexecution', 'flexecution')
    configuration = JsonFileConfigurationProvider(os.getcwd() + '/config.json')
    tokens = EnvironmentTokenProvider()
    server = Server(logger, configuration, tokens, 'testflexecution2')
    server.start()

if __name__ == "__main__":
    main()
