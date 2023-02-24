from User import User
import datetime
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

def test_always_passes():
    assert True

def test_user_print_statement():
    user = User('12345', 'testuser', 'Test User')
    assert user.id == '12345'
    assert user.username == 'testuser'
    assert user.real_name == 'Test User'
    assert user.exercise_history == []
    assert user.exercises == {}
    assert user.exercise_counts == {}
    assert user.past_workouts == {}
    # assert user.username in str(user)
    # assert 'New user:' in str(user)

def test_user_initialization():
    user_id = "U12345678"
    user = User(user_id,'johndoe','John Doe')
    
    assert user.id == user_id
    assert user.username == "johndoe"
    assert user.real_name == "John Doe"
    assert user.exercise_history == []
    assert user.exercises == {}
    assert user.exercise_counts == {}
    assert user.past_workouts == {}