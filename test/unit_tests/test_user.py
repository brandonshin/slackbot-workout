from slackbot_workout.user import User

class TestUser(object):
    def test_init(self):
        u = User('id', 'un', 'rn')
        assert u.id == 'id'
        assert u.username == 'un'
        assert u.real_name == 'rn'
        assert u.total_exercises() == 0

    def test_total_exercises(self):
        u = User('id', 'un', 'rn')
        assert u.total_exercises() == 0
        u.add_exercise('eid1', 3)
        assert u.total_exercises() == 1
        u.add_exercise('eid1', 6)
        assert u.total_exercises() == 2
        u.add_exercise('eid2', 6)
        assert u.total_exercises() == 3
        u.add_exercise('eid2', 0)
        assert u.total_exercises() == 3

    def test_get_exercise_count(self):
        u = User('id', 'un', 'rn')
        assert u.get_exercise_count('eid1') == 0
        u.add_exercise('eid1', 3)
        assert u.get_exercise_count('eid1') == 1
        u.add_exercise('eid1', 6)
        assert u.get_exercise_count('eid1') == 2
        u.add_exercise('eid2', 6)
        assert u.get_exercise_count('eid1') == 2
        u.add_exercise('eid1', 0)
        assert u.get_exercise_count('eid1') == 2

    def test_has_done_exercise(self):
        u = User('id', 'un', 'rn')
        assert u.has_done_exercise('eid1') == False
        assert u.has_done_exercise('eid2') == False
        u.add_exercise('eid1', 5)
        assert u.has_done_exercise('eid1') == True
        assert u.has_done_exercise('eid2') == False
        u.add_exercise('eid2', 0)
        assert u.has_done_exercise('eid1') == True
        assert u.has_done_exercise('eid2') == False
