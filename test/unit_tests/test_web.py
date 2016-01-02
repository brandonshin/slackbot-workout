import mock

from slackbot_workout.manager import UserManager
from slackbot_workout.configurators import InMemoryConfigurationProvider
from slackbot_workout.user import User
from slackbot_workout.web import FlexbotWebServer

def get_sample_config():
    return InMemoryConfigurationProvider({
        'botName': 'testbot',
        'channelName': 'testchannel',
        'exercises': [{
            'id': 0,
            'name': 'exercise1',
            'info': 'exercise1 info'
        }, {
            'id': 1,
            'name': 'exercise2',
            'info': 'exercise2 info'
        }]
    })

def get_server():
    um = mock.Mock(spec=UserManager)
    config = get_sample_config()
    server = FlexbotWebServer(um, config)
    return (um, server)

class TestWeb(object):
    def test_init(self):
        _, server = get_server()
        assert server.bot_name == 'testbot'
        assert server.channel_name == 'testchannel'

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

    def test_flex_handler_bad_message(self):
        _, server = get_server()
        result = server.flex(user_id='UREALUSER', text='testbot notarealmessage')
        assert result == None
