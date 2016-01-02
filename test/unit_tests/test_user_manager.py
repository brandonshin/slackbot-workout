import mock

from slackbot_workout.manager import UserManager
from slackbot_workout.configurators import InMemoryConfigurationProvider

def get_sample_config():
    return InMemoryConfigurationProvider({
        'exercises': [{
            'id': 'eid1',
            'name': 'exercise 1'
        }, {
            'id': 'eid2',
            'name': 'exercise 2'
        }]
    })

def make_user_manager(mock_api):
    return UserManager(mock_api, get_sample_config())

def get_mock_api():
    def get_members():
        return ['uid1', 'uid2']
    def get_user_info(user_id):
        if user_id == 'uid1':
            return {
                'name': 'User1',
                'profile': {
                    'real_name': 'User 1'
                }
            }
        elif user_id == 'uid2':
            return {
                'name': 'User2',
                'profile': {
                    'real_name': 'User 2'
                }
            }
        else:
            return None
    def is_active(user_id):
        if user_id == 'uid1':
            return True
        else:
            return False

    mock_api = mock.Mock()
    mock_api.get_members = get_members
    mock_api.get_user_info = get_user_info
    mock_api.is_active = is_active

    return mock_api

class TestUserManager(object):
    def test_init(self):
        mock_api = get_mock_api()
        um = make_user_manager(mock_api)
        assert um.users == {}
        assert um.exercises == get_sample_config().get_configuration()['exercises']

    def test_fetch_users(self):
        mock_api = get_mock_api()
        um = make_user_manager(mock_api)
        um.fetch_users()
        assert 'uid1' in um.users
        assert 'uid2' in um.users

    def test_fetch_active_users(self):
        mock_api = get_mock_api()
        um = make_user_manager(mock_api)
        active_users = um.fetch_active_users()
        assert len(active_users) == 1
        assert active_users[0].id == 'uid1'

    def test_clear_users(self):
        mock_api = get_mock_api()
        um = make_user_manager(mock_api)
        um.fetch_users()
        assert 'uid1' in um.users
        assert 'uid2' in um.users
        um.clear_users()
        assert len(um.users) == 0

