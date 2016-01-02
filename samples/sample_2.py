from slackbot_workout.loggers import StdOutLogger
from slackbot_workout.configurators import InMemoryTokenProvider, JsonFileConfigurationProvider
from slackbot_workout.server import Server

import os

def main():
    logger = StdOutLogger()
    config = JsonFileConfigurationProvider(os.getcwd() + '/config.json')
    tokens = InMemoryTokenProvider('xoxp-2499669547-10707224704-15892141524-4b7e5a03b7')
    server = Server(logger, config, tokens)
    server.start()

if __name__ == "__main__":
    main()
