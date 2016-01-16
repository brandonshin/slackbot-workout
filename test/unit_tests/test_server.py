from mock import Mock, patch

from flexbot.api import FlexbotApiClient
from flexbot.bot import Bot
from flexbot.configurators import InMemoryConfigurationProvider
from flexbot.exercise import Exercise
from flexbot.loggers import BaseLogger
from flexbot.manager import UserManager
from flexbot.server import Server
from flexbot.user import User
from flexbot.web import FlexbotWebServer

def sample_config():
    return InMemoryConfigurationProvider({
        'debug': False,
        'enable_acknowledgment': True
    })

sample_exercise = Exercise('exercise1', 30, 40, 'reps', '')

sample_users = [
    User('id1', 'username1', 'real name', '1'),
    User('id2', 'username2', 'real name', '2')
]

def get_server_and_mocks():
    logger = Mock(spec=BaseLogger)
    config = sample_config()
    api = Mock(spec=FlexbotApiClient)
    um = Mock(spec=UserManager)
    bot = Mock(spec=Bot)
    web = Mock(spec=FlexbotWebServer)
    server = Server(config, workout_logger=logger, slack_api=api, user_manager=um, bot=bot,
            web_server=web)
    return {
        'api': api,
        'bot': bot,
        'logger': logger,
        'server': server,
        'user_manager': um,
        'web_server': web
    }

class TestServer(object):
    @patch('flexbot.util.time')
    def test_is_first_office_hours(self, mock_time):
        server_and_mocks = get_server_and_mocks()
        server = server_and_mocks['server']
        bot = server_and_mocks['bot']
        um = server_and_mocks['user_manager']
        bot.select_exercise_and_start_time.return_value = (sample_exercise, 30, 5)
        bot.assign_exercise.return_value = [sample_users[0]]

        server._workout_step(False, True)

        um.clear_users.assert_called_once_with()
        bot.select_exercise_and_start_time.assert_called_once_with()
        mock_time.sleep.assert_called_once_with(300)

    @patch('flexbot.util.time')
    def test_first_not_office_hours(self, mock_time):
        server_and_mocks = get_server_and_mocks()
        server = server_and_mocks['server']
        um = server_and_mocks['user_manager']
        bot = server_and_mocks['bot']

        server._workout_step(True, False)

        um.stats.assert_called_once_with()
        mock_time.sleep.assert_called_once_with(300)
        bot.assign_exercise.assert_not_called()
        bot.select_exercise_and_start_time.assert_not_called()

