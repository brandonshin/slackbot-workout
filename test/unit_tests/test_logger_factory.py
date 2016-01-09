import mock

from slackbot_workout.configurators import ConfigurationProvider
from slackbot_workout.constants import Constants
from slackbot_workout.logger_factory import LoggerFactory
from slackbot_workout import loggers

def get_mock_config(logger_type=Constants.IN_MEMORY_LOGGER, settings={}):
    mock_config = mock.Mock(spec=ConfigurationProvider)
    mock_config.workout_logger_type.return_value = logger_type
    mock_config.workout_logger_settings.return_value = settings
    return mock_config

class TestLoggerFactory(object):
    def test_in_memory(self):
        mock_config = get_mock_config()
        logger_factory = LoggerFactory(mock_config)
        logger = logger_factory.get_logger()
        assert type(logger) == loggers.InMemoryLogger

    def test_csv(self):
        mock_config = get_mock_config(logger_type=Constants.CSV_LOGGER)
        logger_factory = LoggerFactory(mock_config)
        logger = logger_factory.get_logger()
        assert type(logger) == loggers.CsvLogger

    @mock.patch('slackbot_workout.loggers.psycopg2')
    def test_postgres(self, fake_db_api):
        settings = {
            'dbname': 'flexecution',
            'tablename': 'flexecution'
        }
        mock_config = get_mock_config(logger_type=Constants.POSTGRES_DATABASE_LOGGER,
                settings = settings)
        logger_factory = LoggerFactory(mock_config)
        logger = logger_factory.get_logger()
        assert type(logger) == loggers.PostgresDatabaseLogger

