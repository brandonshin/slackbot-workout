from User import User
import datetime
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

def test_always_passes():
    assert True

def user():
    return User("1234567890") # replace with a valid user ID

# def test_fetch_names(user):
#     assert user.username == "test_user"
#     assert user.real_name == "Test User"

def test_add_exercise(user):
    exercise = {
        "id": 1,
        "name": "Push-ups",
        "units": "reps"
    }
    user.addExercise(exercise, 10)
#     assert user.exercises == {1: 10}
#     assert user.exercise_counts == {1: 1}
#     assert user.exercise_history == [[datetime.datetime.now().isoformat(), 1, "Push-ups", 10, "reps"]]

