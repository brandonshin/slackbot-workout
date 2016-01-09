from mock import Mock

from slackbot_workout.api import SlackbotApi
from slackbot_workout.bot import Bot
from slackbot_workout.configurators import InMemoryConfigurationProvider
from slackbot_workout.exercise import Exercise
from slackbot_workout.loggers import BaseLogger
from slackbot_workout.manager import UserManager
from slackbot_workout.user import User

exercises = [
    Exercise(0, "pushups", 15, 20, "reps", ''),
    Exercise(1, "planks", 40, 60, "seconds", '')
]


def get_sample_config():
    return InMemoryConfigurationProvider({
        "office_hours": {
            "on": False,
            "begin": 10,
            "end": 18
        },

        "debug": False,

        "callouts": {
            "time_between": {
                "min_time": 10,
                "max_time": 100,
                "units": "minutes"
            },
            "num_people": 1,
            "group_callout_chance": 0.1
        },

        "user_exercise_limit": 3
    }, exercises)


def get_sample_bot():
    api = Mock(spec=SlackbotApi)
    logger = Mock(spec=BaseLogger)
    config = get_sample_config()
    um = Mock(spec=UserManager)
    bot = Bot(api, logger, config, um)
    return (um, bot)

def eligible_users():
    return [
        User('slackid1', 'username1', 'real name', '1'),
        User('slackid2', 'username2', 'real name', '2'),
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
        exercises = config.exercises()
        min_time = config.min_time_between_callouts()
        max_time = config.max_time_between_callouts()
        _, bot = get_sample_bot()
        exercise, reps, mins_to_exercise = bot._select_exercise_and_start_time(eligible_users())
        assert exercise.name in map(lambda e: e.name, exercises)
        assert min_time <= mins_to_exercise <= max_time

