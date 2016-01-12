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

    mock_api = mock.Mock()
    mock_api.get_members = get_members
    mock_api.get_user_info = get_user_info
    mock_api.is_active = is_active

    return mock_api

class TestUserManager(object):
    def test_fetch_users(self):
        mock_api = get_mock_api()
        um = make_user_manager(mock_api)
        um.fetch_users()
        assert 'uid1' in um.users
        assert 'uid2' in um.users
        assert 'uid3' in um.users
        assert um.users['uid3'].firstname == ''
        assert um.users['uid3'].lastname == ''

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

    def test_get_firstname(self):
        mock_api = get_mock_api()
        um = make_user_manager(mock_api)
        um.fetch_users()
        assert um.get_firstname('uid1') == 'User'
        assert um.get_firstname('uid0') == None

    def test_get_username(self):
        mock_api = get_mock_api()
        um = make_user_manager(mock_api)
        um.fetch_users()
        assert um.get_username('uid1') == 'User1'
        assert um.get_username('uid0') == None

    def test_current_winners(self):
        mock_api = get_mock_api()
        um = make_user_manager(mock_api)
        assert len(um.get_current_winners()) == 0
        um.add_to_current_winners('uid1', mock.Mock(), 30)
        assert len(um.get_current_winners()) == 1
        um.remove_from_current_winners('uid1')
        assert len(um.get_current_winners()) == 0

