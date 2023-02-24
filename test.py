from User import User
import datetime
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

def test_always_passes():
    assert True

def test_user_print_statement():
    user = User('12345')
    assert user.real_name in str(user)
    # assert user.username in str(user)
    # assert 'New user:' in str(user)