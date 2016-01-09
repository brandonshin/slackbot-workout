import mock

from slackbot_workout.configurators import InMemoryConfigurationProvider
from slackbot_workout.constants import Constants
from slackbot_workout.exercise import Exercise
from slackbot_workout.manager import UserManager
from slackbot_workout.util import StatementRenderer
from slackbot_workout.web import FlexbotWebServer

exercises = [
    Exercise(0, 'exercise1', 30, 40, 'reps', 'exercise1 info'),
    Exercise(1, 'exercise2', 30, 40, 'reps', 'exercise2 info'),
]

def get_sample_config(enable_acknowledgment):
    return InMemoryConfigurationProvider({
        'bot_name': 'testbot',
        'channel_name': 'testchannel',
        'enable_acknowledgment': enable_acknowledgment
    }, exercises)

def get_server(enable_acknowledgment=True):
    um = mock.Mock(spec=UserManager)
    config = get_sample_config(enable_acknowledgment)
    ack_handler = mock.Mock()
    server = FlexbotWebServer(um, ack_handler, config)
    return {
        'ack_handler': ack_handler,
        'user_manager': um,
        'server': server
    }

class TestWeb(object):
    def test_flex_handler_from_slackbot(self):
        server = get_server()['server']
        result = server.flex(user_id='USLACKBOT', text='testbot help')
        assert result == None

    def test_flex_handler_help(self):
        server = get_server()['server']
        result = server.flex(user_id='UREALUSER', text='testbot help')
        assert "Welcome to testchannel! I am testbot" in result['text']

    def test_flex_handler_exercises(self):
        server = get_server()['server']
        result = server.flex(user_id='UREALUSER', text='testbot exercises')
        assert "The currently supported exercises are:" in result['text']
        assert "exercise1" in result['text']
        assert "exercise2" in result['text']

    def test_flex_handler_exercise_info(self):
        server = get_server()['server']
        result = server.flex(user_id='UREALUSER', text='testbot info exercise1')
        assert 'exercise1 info' in result['text']
        assert 'exercise2 info' not in result['text']

    def test_flex_handler_done_success(self):
        test_server = get_server()
        ack_handler = test_server['ack_handler']
        um = test_server['user_manager']
        server = test_server['server']
        ack_handler.acknowledge_winner.return_value = Constants.ACKNOWLEDGE_SUCCEEDED
        um.get_firstname.return_value = 'Real'
        result = server.flex(user_id='UREALUSER', text='testbot done')
        assert len(filter(lambda u: result['text'] == StatementRenderer(u).render_statement('Real'),
            server.SUCCESS_STATEMENTS)) == 1

    def test_flex_handler_done_with_bang(self):
        test_server = get_server()
        ack_handler = test_server['ack_handler']
        um = test_server['user_manager']
        server = test_server['server']
        ack_handler.acknowledge_winner.return_value = Constants.ACKNOWLEDGE_SUCCEEDED
        um.get_firstname.return_value = 'Real'
        result = server.flex(user_id='UREALUSER', text='testbot done!')
        assert len(filter(lambda u: result['text'] == StatementRenderer(u).render_statement('Real'),
            server.SUCCESS_STATEMENTS)) == 1

    def test_flex_handler_done_failure(self):
        test_server = get_server()
        ack_handler = test_server['ack_handler']
        um = test_server['user_manager']
        server = test_server['server']
        um.get_firstname.return_value = 'Fake'
        ack_handler.acknowledge_winner.return_value = Constants.ACKNOWLEDGE_FAILED
        result = server.flex(user_id='UFAKEUSER', text='testbot done')
        assert len(filter(lambda u: result['text'] == StatementRenderer(u).render_statement('Fake'),
            server.FAILURE_STATEMENTS)) == 1

    def test_flex_handler_done_disabled(self):
        test_server = get_server()
        ack_handler, server = test_server['ack_handler'], test_server['server']
        server.flex(user_id='UREALUSER', text='testbot done realuser')
        ack_handler.acknowledge_winner.assert_never_called()

    def test_flex_handler_bad_message(self):
        server = get_server()['server']
        result = server.flex(user_id='UREALUSER', text='testbot notarealmessage')
        assert result == None
