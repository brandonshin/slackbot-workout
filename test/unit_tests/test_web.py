import mock

from slackbot_workout.exercise import Exercise
from slackbot_workout.manager import UserManager
from slackbot_workout.configurators import InMemoryConfigurationProvider
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
    return (ack_handler, server)

class TestWeb(object):
    def test_flex_handler_from_slackbot(self):
        _, server = get_server()
        result = server.flex(user_id='USLACKBOT', text='testbot help')
        assert result == None

    def test_flex_handler_help(self):
        _, server = get_server()
        result = server.flex(user_id='UREALUSER', text='testbot help')
        assert "Welcome to testchannel! I am testbot" in result['text']

    def test_flex_handler_exercises(self):
        _, server = get_server()
        result = server.flex(user_id='UREALUSER', text='testbot exercises')
        assert "The currently supported exercises are:" in result['text']
        assert "exercise1" in result['text']
        assert "exercise2" in result['text']

    def test_flex_handler_exercise_info(self):
        _, server = get_server()
        result = server.flex(user_id='UREALUSER', text='testbot info exercise1')
        assert 'exercise1 info' in result['text']
        assert 'exercise2 info' not in result['text']

    def test_flex_handler_done(self):
        ack_handler, server = get_server()
        server.flex(user_id='UREALUSER', text='testbot done realuser')
        ack_handler.acknowledge_winner.assert_called_once_with('UREALUSER')

    def test_flex_handler_done_disabled(self):
        ack_handler, server = get_server(enable_acknowledgment=False)
        server.flex(user_id='UREALUSER', text='testbot done realuser')
        ack_handler.acknowledge_winner.assert_never_called()

    def test_flex_handler_bad_message(self):
        _, server = get_server()
        result = server.flex(user_id='UREALUSER', text='testbot notarealmessage')
        assert result == None
