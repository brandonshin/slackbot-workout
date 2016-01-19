import mock

from flexbot.api import FlexbotApiClient
from flexbot.configurators import InMemoryConfigurationProvider
from flexbot.constants import Constants
from flexbot.exercise import Exercise
from flexbot.loggers import BaseLogger
from flexbot.manager import UserManager

def get_sample_exercises():
    return [
        Exercise('pushups', 30, 40, 'reps', ''),
        Exercise('situps', 30, 40, 'reps', '')
    ]

def get_sample_config(enable_acknowledgment):
    return InMemoryConfigurationProvider({
        "enable_acknowledgment": enable_acknowledgment
    }, exercises=get_sample_exercises())

def make_user_manager(enable_acknowledgment=True):
    mock_api = get_mock_api()
    logger = mock.Mock(spec=BaseLogger)
    um = UserManager(mock_api, get_sample_config(enable_acknowledgment), logger)
    return {
        'user_manager': um,
        'logger': logger
    }

def get_mock_api():
    def get_members():
        return ['uid1', 'uid2', 'uid3']
    def get_user_info(user_id):
        if user_id == 'uid1':
            return {
                'name': 'User1',
                'profile': {
                    'first_name': 'User',
                    'last_name': '1'
                }
            }
        elif user_id == 'uid2':
            return {
                'name': 'User2',
                'profile': {
                    'first_name': 'User',
                    'last_name': '2'
                }
            }
        elif user_id == 'uid3':
            return {
                'name': 'User3',
                'profile': {
                }
            }
        else:
            return None
    def is_active(user_id):
        if user_id == 'uid1':
            return True
        else:
            return False

    mock_api = mock.Mock(spec=FlexbotApiClient)
    mock_api.get_members = get_members
    mock_api.get_user_info = get_user_info
    mock_api.is_active = is_active

    return mock_api

class TestUserManager(object):
    def test_fetch_users(self):
        um_and_mocks = make_user_manager()
        um = um_and_mocks['user_manager']
        um.fetch_users()
        assert 'uid1' in um.users
        assert 'uid2' in um.users
        assert 'uid3' in um.users
        assert um.users['uid3'].firstname == ''
        assert um.users['uid3'].lastname == ''

    def test_fetch_active_users(self):
        um_and_mocks = make_user_manager()
        um = um_and_mocks['user_manager']
        active_users = um.fetch_active_users()
        assert len(active_users) == 1
        assert active_users[0] == 'uid1'

    def test_clear_users(self):
        um_and_mocks = make_user_manager()
        um = um_and_mocks['user_manager']
        um.fetch_users()
        assert 'uid1' in um.users
        assert 'uid2' in um.users
        um.clear_users()
        assert len(um.users) == 0

    def test_get_firstname(self):
        um_and_mocks = make_user_manager()
        um = um_and_mocks['user_manager']
        um.fetch_users()
        assert um.get_firstname('uid1') == 'User'
        assert um.get_firstname('uid0') == None

    def test_get_username(self):
        um_and_mocks = make_user_manager()
        um = um_and_mocks['user_manager']
        um.fetch_users()
        assert um.get_username('uid1') == 'User1'
        assert um.get_username('uid0') == None

    def test_current_winners(self):
        um_and_mocks = make_user_manager()
        um = um_and_mocks['user_manager']
        logger = um_and_mocks['logger']
        um.get_current_winners()
        logger.get_current_winners.assert_called_once_with()

    def test_get_eligible_users(self):
        um_and_mocks = make_user_manager()
        um = um_and_mocks['user_manager']
        logger = um_and_mocks['logger']
        logger.get_todays_exercises.return_value = {
            'uid1': [{
                'exercise': 'pushups',
                'reps': 30
            }]
        }
        logger.get_current_winners.return_value = {}
        eligible_users = um.get_eligible_users()
        assert len(eligible_users) == 1
        assert eligible_users[0] == 'uid1'

    def test_acknowledge_winner_failure(self):
        um_and_mocks = make_user_manager()
        um = um_and_mocks['user_manager']
        logger = um_and_mocks['logger']
        logger.finish_exercise.return_value = None

        result = um.acknowledge_winner('uid1')

        assert result == Constants.ACKNOWLEDGE_FAILED
        logger.log_exercise.assert_not_called()

    def test_acknowledge_winner_success(self):
        um_and_mocks = make_user_manager()
        um = um_and_mocks['user_manager']
        logger = um_and_mocks['logger']
        logger.finish_exercise.return_value = {
            'exercise': 'pushups',
            'reps': 30
        }

        result = um.acknowledge_winner('uid1')

        assert result == Constants.ACKNOWLEDGE_SUCCEEDED
        assert logger.log_exercise.call_count == 1

    def test_mark_winner_ack_enabled(self):
        um_and_mocks = make_user_manager()
        um = um_and_mocks['user_manager']
        logger = um_and_mocks['logger']
        exercise = get_sample_exercises()[0]
        um.mark_winner('uid1', exercise, 30)
        logger.add_exercise.assert_called_once_with('uid1', exercise, 30)
        logger.log_exercise.assert_not_called()

    def test_mark_winner_ack_disabled(self):
        um_and_mocks = make_user_manager(enable_acknowledgment=False)
        um = um_and_mocks['user_manager']
        logger = um_and_mocks['logger']
        exercise = get_sample_exercises()[0]
        um.mark_winner('uid1', exercise, 30)
        logger.add_exercise.assert_not_called()
        logger.log_exercise.assert_called_once_with('uid1', exercise, 30)

    def test_add_exercise_for_user(self):
        um_and_mocks = make_user_manager(enable_acknowledgment=False)
        um = um_and_mocks['user_manager']
        logger = um_and_mocks['logger']
        exercise = get_sample_exercises()[0]
        um.add_exercise_for_user('uid1', exercise, 30)
        logger.log_exercise.assert_called_once_with('uid1', exercise, 30)

    def test_total_exercises_for_user(self):
        um_and_mocks = make_user_manager(enable_acknowledgment=False)
        um = um_and_mocks['user_manager']
        logger = um_and_mocks['logger']
        logger.get_todays_exercises.return_value = {
            'uid1': [{
                'exercise': 'pushups',
                'reps': 30
            }]
        }
        assert um.total_exercises_for_user('uid1') == 1
        assert um.total_exercises_for_user('uid3') == 0

    def test_exercise_count_for_user(self):
        um_and_mocks = make_user_manager(enable_acknowledgment=False)
        um = um_and_mocks['user_manager']
        logger = um_and_mocks['logger']
        logger.get_todays_exercises.return_value = {
            'uid1': [{
                'exercise': 'pushups',
                'reps': 30
            }]
        }
        sample_exercises = get_sample_exercises()
        assert um.exercise_count_for_user('uid1', sample_exercises[0]) == 1
        assert um.exercise_count_for_user('uid1', sample_exercises[1]) == 0
        assert um.exercise_count_for_user('uid3', sample_exercises[0]) == 0

    def test_user_has_done_exercise(self):
        um_and_mocks = make_user_manager(enable_acknowledgment=False)
        um = um_and_mocks['user_manager']
        logger = um_and_mocks['logger']
        logger.get_todays_exercises.return_value = {
            'uid1': [{
                'exercise': 'pushups',
                'reps': 30
            }]
        }
        sample_exercises = get_sample_exercises()
        assert um.user_has_done_exercise('uid1', sample_exercises[0])
        assert not um.user_has_done_exercise('uid1', sample_exercises[1])
        assert not um.user_has_done_exercise('uid3', sample_exercises[0])
