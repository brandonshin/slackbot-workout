import os

from flexbot.exercise import Exercise
from flexbot.loggers import CsvLogger

exercises = [
    Exercise('pushups', 30, 40, 'reps', ''),
    Exercise('situps', 30, 40, 'reps', '')
]

class TestCsvLogger(object):
    def teardown(self):
        logfiles = [f for f in os.listdir('.') if f.endswith('.csv')]
        for f in logfiles:
            os.remove(f)

    def get_logger(self):
        return CsvLogger()

    def test_log_exercise(self):
        logger = self.get_logger()
        filename = logger.csv_filename()

        logger.log_exercise('miles', exercises[0], 30)
        assert os.path.exists(filename)
        with open(filename, 'r') as f:
            contents = f.read().strip().split("\n")
            assert len(contents) == 1

        logger.log_exercise('greg', exercises[1], 40)
        assert os.path.exists(filename)
        with open(filename, 'r') as f:
            contents = f.read().strip().split("\n")
            assert len(contents) == 2

    def test_get_todays_exercises(self):
        logger = self.get_logger()

        logger.log_exercise('miles', exercises[0], 30)
        logger.log_exercise('greg', exercises[1], 40)

        todays_exercises = logger.get_todays_exercises()

        assert 'miles' in todays_exercises
        assert todays_exercises['miles'] == [{'exercise': 'pushups', 'reps': 30}]
        assert 'greg' in todays_exercises
        assert todays_exercises['greg'] == [{'exercise': 'situps', 'reps': 40}]

    def test_add_exercise_and_get_current_winners(self):
        logger = self.get_logger()

        logger.add_exercise('uid1', exercises[0], 30)
        logger.add_exercise('uid2', exercises[1], 35)
        logger.add_exercise('uid2', exercises[0], 40)
        winners = logger.get_current_winners()

        assert 'uid1' in winners
        assert len(winners['uid1']) == 1
        assert winners['uid1'][0]['exercise'] == exercises[0].name
        assert winners['uid1'][0]['reps'] == 30
        assert 'uid2' in winners
        assert len(winners['uid2']) == 2
        assert winners['uid2'][0]['exercise'] == exercises[1].name
        assert winners['uid2'][0]['reps'] == 35
        assert winners['uid2'][1]['exercise'] == exercises[0].name
        assert winners['uid2'][1]['reps'] == 40
        assert 'uid3' not in winners

    def test_finishe_exercise(self):
        logger = self.get_logger()

        logger.add_exercise('uid1', exercises[0], 30)
        logger.add_exercise('uid2', exercises[1], 35)
        logger.finish_exercise('uid1')
        winners = logger.get_current_winners()

        assert 'uid1' not in winners
        assert len(winners['uid2']) == 1
        assert winners['uid2'][0]['exercise'] == exercises[1].name
        assert winners['uid2'][0]['reps'] == 35
