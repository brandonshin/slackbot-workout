from mock import Mock

from flexbot.api import FlexbotApiClient
from flexbot.bot import Bot
from flexbot.configurators import InMemoryConfigurationProvider
from flexbot.exercise import Exercise
from flexbot.manager import UserManager
from flexbot.user import User

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
            "group_callout_chance": 0
        },

        "user_exercise_limit": 3,
        "enable_acknowledgment": True
    }, exercises)

def get_sample_bot():
    api = Mock(spec=FlexbotApiClient)
    config = get_sample_config()
    um = Mock(spec=UserManager)
    bot = Bot(api, config, um)
    return {
        'user_manager': um,
        'bot': bot
    }

class TestBot(object):
    def test_select_next_time_interval(self):
        bot_and_mocks = get_sample_bot()
        bot = bot_and_mocks['bot']
        um = bot_and_mocks['user_manager']
        um.total_exercises_for_user.return_value = 0
        users = map(lambda u: u.id, active_users())
        interval = bot.select_next_time_interval(users)
        assert isinstance(interval, int) or (isinstance(interval, float) and interval.is_integer())

    def test_select_exercise_and_start_time(self):
        config = get_sample_config()
        exercises = config.exercises()
        min_time = config.min_time_between_callouts()
        max_time = config.max_time_between_callouts()
        bot_and_mocks = get_sample_bot()
        bot = bot_and_mocks['bot']
        um = bot_and_mocks['user_manager']
        um.total_exercises_for_user.return_value = 0
        users = map(lambda u: u.id, active_users())
        exercise, reps, mins_to_exercise = bot._select_exercise_and_start_time(users)
        assert exercise.name in map(lambda e: e.name, exercises)
        assert min_time <= mins_to_exercise <= max_time

    def test_assign_exercise_with_ack(self):
        bot_and_mocks = get_sample_bot()
        bot = bot_and_mocks['bot']
        um = bot_and_mocks['user_manager']
        users = active_users()
        um.get_eligible_users.return_value = map(lambda u: u.id, users)
        um.user_has_done_exercise.return_value = False
        um.total_exercises_for_user.return_value = 0

        bot.assign_exercise(exercises[0], 30)

        assert um.mark_winner.call_count == 1

    def test_get_lottery_list(self):
        exercise_list = []
        def make_mock_user(user_id, exercise_count):
            u = Mock(spec=User)
            u.id = user_id
            exercise_list.append((user_id, exercise_count))
            return u
        ulist = [make_mock_user(uid, exercises) for (uid, exercises) in [('uid1', 2), ('uid2', 1)]]
        uidlist = map(lambda u: u.id, ulist)
        def total_exercises(user_id):
            try:
                filtered = filter(lambda u: u[0] == user_id, exercise_list)
                return filtered[0][1]
            except:
                return 0
        bot_and_mocks = get_sample_bot()
        bot = bot_and_mocks['bot']
        um = bot_and_mocks['user_manager']
        um.total_exercises_for_user = total_exercises
        lottery_list = bot.get_lottery_list(uidlist)
        assert len(filter(lambda u: u == 'uid1', lottery_list)) == 1
        assert len(filter(lambda u: u == 'uid2', lottery_list)) == 2
