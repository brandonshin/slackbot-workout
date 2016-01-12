from mock import Mock

from slackbot_workout.api import SlackbotApi
from slackbot_workout.bot import Bot
from slackbot_workout.configurators import InMemoryConfigurationProvider
from slackbot_workout.exercise import Exercise
from slackbot_workout.loggers import BaseLogger
from slackbot_workout.manager import UserManager
from slackbot_workout.user import User

exercises = [
    Exercise("pushups", 15, 20, "reps", ''),
    Exercise("planks", 40, 60, "seconds", '')
]

def active_users():
    return [
        User('slackid1', 'username1', 'real name', '1'),
        User('slackid2', 'username2', 'real name', '2')
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

        "user_exercise_limit": 3,
        "enable_acknowledgment": True
    }, exercises)

def get_sample_bot():
    api = Mock(spec=SlackbotApi)
    logger = Mock(spec=BaseLogger)
    config = get_sample_config()
    um = Mock(spec=UserManager)
    bot = Bot(api, logger, config, um)
    return {
        'user_manager': um,
        'logger': logger,
        'bot': bot
    }

class TestBot(object):
    def test_init(self):
        bot = get_sample_bot()['bot']
        assert bot.user_queue == []

    def test_select_next_time_interval(self):
        bot = get_sample_bot()['bot']
        interval = bot.select_next_time_interval(active_users())
        assert isinstance(interval, int) or (isinstance(interval, float) and interval.is_integer())

    def test_select_exercise_and_start_time(self):
        config = get_sample_config()
        exercises = config.exercises()
        min_time = config.min_time_between_callouts()
        max_time = config.max_time_between_callouts()
        bot = get_sample_bot()['bot']
        exercise, reps, mins_to_exercise = bot._select_exercise_and_start_time(active_users())
        assert exercise.name in map(lambda e: e.name, exercises)
        assert min_time <= mins_to_exercise <= max_time

    def test_assign_exercise_with_ack(self):
        bot_and_mocks = get_sample_bot()
        bot = bot_and_mocks['bot']
        um = bot_and_mocks['user_manager']
        logger = bot_and_mocks['logger']
        users = active_users()
        um.fetch_active_users.return_value = users
        um.get_current_winners.return_value = [(users[0], exercises[0], 10)]

        winners = bot.assign_exercise(exercises[0], 30)

        assert um.add_to_current_winners.call_count == 1
        assert winners[0].total_exercises() == 0
        assert logger.log_exercise.assert_never_called()

    def test_get_eligible_users(self):
        bot_and_mocks = get_sample_bot()
        bot = bot_and_mocks['bot']
        um = bot_and_mocks['user_manager']
        users = active_users()
        um.fetch_active_users.return_value = users
        um.get_current_winners.return_value = [(users[0], exercises[0], 10)]
        eligible_users = bot.get_eligible_users()
        assert eligible_users[0].id == 'slackid2'

    def test_acknowledge_winner(self):
        bot_and_mocks = get_sample_bot()
        bot = bot_and_mocks['bot']
        logger = bot_and_mocks['logger']
        um = bot_and_mocks['user_manager']
        umap = {}
        users = active_users()
        for u in users:
            umap[u.id] = u
        um.users = umap
        winner1 = (users[0].id, exercises[0], 10)
        winner2 = (users[1].id, exercises[1], 20)
        um.get_current_winners.return_value = [winner1, winner2]

        bot.acknowledge_winner('slackid1')

        um.remove_from_current_winners.assert_called_once_with('slackid1')
        logger.log_exercise.assert_called_once_with('slackid1', winner1[1], winner1[2])
