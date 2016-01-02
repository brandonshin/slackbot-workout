from slackbot_workout.loggers import PostgresDatabaseLogger
from slackbot_workout.configurators import InMemoryTokenProvider, JsonFileConfigurationProvider
from slackbot_workout.server import Server
import os

def main():
    logger = PostgresDatabaseLogger('flexecution', 'flexecution',
            host='flexecution-postgres.chlee7xx28jo.us-west-2.rds.amazonaws.com', port=5432,
            user='flexecution', password='DcHqIxAE^IbgX52K9!5R')
    config = JsonFileConfigurationProvider(os.getcwd() + '/config.json')
    tokens = InMemoryTokenProvider('xoxp-2499669547-10707224704-15892141524-4b7e5a03b7')
    server = Server(logger, config, tokens)
    server.start()

if __name__ == "__main__":
    main()
