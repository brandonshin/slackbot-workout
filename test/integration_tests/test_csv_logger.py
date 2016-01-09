import os

from slackbot_workout.exercise import Exercise
from slackbot_workout.loggers import CsvLogger

exercises = [
    Exercise(1, 'pushups', 30, 40, 'reps', ''),
    Exercise(1, 'situps', 30, 40, 'reps', '')
]

class TestCsvLogger(object):
    def teardown(self):
        logfiles = [f for f in os.listdir('.') if f.endswith('.csv')]
        for f in logfiles:
            os.remove(f)

    def test_log_exercise(self):
        logger = CsvLogger()
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
        logger = CsvLogger()

        logger.log_exercise('miles', exercises[0], 30)
        logger.log_exercise('greg', exercises[1], 40)

        todays_exercises = logger.get_todays_exercises()

        assert 'miles' in todays_exercises
        assert todays_exercises['miles'] == [{'exercise': 'pushups', 'reps': 30}]
        assert 'greg' in todays_exercises
        assert todays_exercises['greg'] == [{'exercise': 'situps', 'reps': 40}]
