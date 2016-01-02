import os

from slackbot_workout.loggers import CsvLogger

class TestCsvLogger(object):
    def teardown(self):
        logfiles = [f for f in os.listdir('.') if f.endswith('.csv')]
        for f in logfiles:
            os.remove(f)

    def test_log_exercise(self):
        logger = CsvLogger()
        filename = logger.csv_filename()

        logger.log_exercise('miles', 'pushups', 30, 'reps')
        assert os.path.exists(filename)
        with open(filename, 'r') as f:
            contents = f.read().strip().split("\n")
            assert len(contents) == 1

        logger.log_exercise('greg', 'situps', 40, 'reps')
        assert os.path.exists(filename)
        with open(filename, 'r') as f:
            contents = f.read().strip().split("\n")
            assert len(contents) == 2

    def test_get_todays_exercises(self):
        logger = CsvLogger()

        logger.log_exercise('miles', 'pushups', 30, 'reps')
        logger.log_exercise('greg', 'situps', 40, 'reps')

        exercises = logger.get_todays_exercises()

        assert 'miles' in exercises
        assert exercises['miles'] == [{'exercise': 'pushups', 'reps': 30}]
        assert 'greg' in exercises
        assert exercises['greg'] == [{'exercise': 'situps', 'reps': 40}]
