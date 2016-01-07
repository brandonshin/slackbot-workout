from mock import Mock, patch

from slackbot_workout.api import SlackbotApi
from slackbot_workout.bot import Bot
from slackbot_workout.configurators import InMemoryConfigurationProvider, TokenProvider
from slackbot_workout.loggers import BaseLogger
from slackbot_workout.manager import UserManager
from slackbot_workout.server import Server
from slackbot_workout.user import User
from slackbot_workout.web import FlexbotWebServer

def sample_config():
    return InMemoryConfigurationProvider({
        'debug': False,
        'enable_acknowledgment': True
    })

def sample_exercise():
    return {
        'id': 1,
        'name': 'exercise1',
        'units': 'reps'
    }

def sample_users():
    return [
        User('id1', 'username1', 'real name 1'),
        User('id2', 'username2', 'real name 2')
    ]

def get_server_and_mocks():
    logger = Mock(spec=BaseLogger)
    config = sample_config()
    token = Mock(spec=TokenProvider)
    api = Mock(spec=SlackbotApi)
    um = Mock(spec=UserManager)
    bot = Mock(spec=Bot)
    web = Mock(spec=FlexbotWebServer)
    server = Server(logger, config, token, slack_api=api, user_manager=um, bot=bot, web_server=web)
    return {
        'api': api,
        'bot': bot,
        'logger': logger,
        'server': server,
        'user_manager': um,
        'web_server': web
    }

class TestServer(object):
    @patch('slackbot_workout.util.time')
    def test_is_first_office_hours(self, mock_time):
        server_and_mocks = get_server_and_mocks()
        server = server_and_mocks['server']
        bot = server_and_mocks['bot']
        um = server_and_mocks['user_manager']
        bot.select_exercise_and_start_time.return_value = (sample_exercise(), 30, 5)
        user = sample_users()[0]
        bot.assign_exercise.return_value = [user]

        server._workout_step(False, True)

        um.clear_users.assert_called_once_with()
        bot.select_exercise_and_start_time.assert_called_once_with()
        mock_time.sleep.assert_called_once_with(300)
        assert len(server.current_winners) == 1 and server.current_winners[0] == user
        assert server.current_exercise == sample_exercise()
        assert server.current_reps == 30

    @patch('slackbot_workout.util.time')
    def test_first_not_office_hours(self, mock_time):
        server_and_mocks = get_server_and_mocks()
        server = server_and_mocks['server']
        um = server_and_mocks['user_manager']
        bot = server_and_mocks['bot']

        server._workout_step(True, False)

        um.stats.assert_called_once_with()
        mock_time.sleep.assert_called_once_with(300)
        bot.assign_exercise.assert_never_called()
        bot.select_exercise_and_start_time.assert_never_called()

    def test_acknowledge_winner(self):
        server_and_mocks = get_server_and_mocks()
        server = server_and_mocks['server']
        logger = server_and_mocks['logger']
        um = server_and_mocks['user_manager']
        users = sample_users()
        umap = {}
        for u in users:
            umap[u.id] = u
        um.users = umap
        server.current_winners = users
        server.current_exercise = sample_exercise()
        server.current_reps = 30

        server.acknowledge_winner('id1')

        assert server.current_winners == filter(lambda u: u.id != 'id1', users)
        logger.log_exercise.assert_called_once_with('id1', 'exercise1', 30, 'reps')
