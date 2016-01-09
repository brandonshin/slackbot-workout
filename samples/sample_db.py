from slackbot_workout.loggers import PostgresDatabaseLogger
from slackbot_workout.configurators import JsonFileConfigurationProvider
from slackbot_workout.server import Server
import os

def main():
    logger = PostgresDatabaseLogger('flexecution', dbname='flexecution',
            host='flexecution-postgres.chlee7xx28jo.us-west-2.rds.amazonaws.com', port=5432,
            user='flexecution', password='DcHqIxAE^IbgX52K9!5R')
    config = JsonFileConfigurationProvider(os.getcwd() + '/config.json')
    server = Server(config, workout_logger=logger)
    server.start()

if __name__ == "__main__":
    main()
