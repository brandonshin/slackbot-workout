from mock import Mock

from slackbot_workout.api import SlackbotApi
from slackbot_workout.bot import Bot
from slackbot_workout.configurators import InMemoryConfigurationProvider
from slackbot_workout.loggers import BaseLogger
from slackbot_workout.manager import UserManager
from slackbot_workout.user import User

def get_sample_config():
    return InMemoryConfigurationProvider( {
        "officeHours": {
            "on": False,
            "begin": 10,
            "end": 18
        },

        "debug": False,

        "callouts": {
            "timeBetween": {
                "minTime": 10,
                "maxTime": 100,
                "units": "minutes"
            },
            "numPeople": 1,
            "groupCalloutChance": 0.1
        },

        "exercises": [
            {
                "id": 0,
                "name": "pushups",
                "minReps": 15,
                "maxReps": 20,
                "units": "rep"
            },
            {
                "id": 1,
                "name": "planks",
                "minReps": 40,
                "maxReps": 60,
                "units": "second"
            },
        ],

        "user_exercise_limit": 3
    })


def get_sample_bot():
    api = Mock(spec=SlackbotApi)
    logger = Mock(spec=BaseLogger)
    config = get_sample_config()
    um = Mock(spec=UserManager)
    bot = Bot(api, logger, config, um)
    return (um, bot)

def eligible_users():
    return [
        User('slackid1', 'username1', 'real name 1'),
        User('slackid2', 'username2', 'real name 2'),
    ]

class TestBot(object):
    def test_init(self):
        _, bot = get_sample_bot()
        assert bot.user_queue == []

    def test_select_next_time_interval(self):
        _, bot = get_sample_bot()
        interval = bot.select_next_time_interval(eligible_users())
        assert isinstance(interval, int) or (isinstance(interval, float) and interval.is_integer())

    def test_select_exercise_and_start_time(self):
        config = get_sample_config()
        exercises = config.get_configuration()['exercises']
        time_range = config.get_configuration()['callouts']['timeBetween']
        _, bot = get_sample_bot()
        exercise, mins_to_exercise = bot._select_exercise_and_start_time(eligible_users())
        assert exercise['name'] in map(lambda e: e['name'], exercises)
        assert time_range['minTime'] <= mins_to_exercise <= time_range['maxTime']

