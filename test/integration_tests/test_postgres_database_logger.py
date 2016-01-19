from flexbot.exercise import Exercise
from flexbot.loggers import PostgresDatabaseLogger, PostgresConnector

exercises = [
    Exercise('pushups', 30, 40, 'reps', ''),
    Exercise('situps', 30, 40, 'reps', '')
]

class TestPostgresDatabaseLogger(PostgresConnector):
    dbname = 'travis_ci_test' # must be kept in sync with .travis.yml
    tablename = 'flexecution'
    winners_table = 'winners'
    kwargs = {'dbname': dbname}

    def teardown(self):
        def clear_tables(cursor):
            cursor.execute("DELETE FROM {}".format(self.tablename))
            cursor.execute("DELETE FROM {}".format(self.winners_table))
        self.with_connection(clear_tables)

    def get_logger(self):
        return PostgresDatabaseLogger(self.tablename, self.winners_table, dbname=self.dbname)

    def test_log_exercise(self):
        logger = self.get_logger()
        logger.log_exercise('miles', exercises[0], 30)

        def get_exercises(cursor):
            cursor.execute("SELECT user_id, exercise, reps FROM {}".format(self.tablename))
            return cursor.fetchall()
        logged_exercises = self.with_connection(get_exercises)
        assert logged_exercises == [('miles', 'pushups', 30)]

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

    def test_finish_exercise(self):
        logger = self.get_logger()

        logger.add_exercise('uid1', exercises[0], 30)
        logger.add_exercise('uid2', exercises[1], 35)
        exercise = logger.finish_exercise('uid1')
        winners = logger.get_current_winners()

        assert 'uid1' not in winners
        assert len(winners['uid2']) == 1
        assert winners['uid2'][0]['exercise'] == exercises[1].name
        assert winners['uid2'][0]['reps'] == 35
        assert exercise != None
        assert exercise['exercise'] == 'pushups'
        assert exercise['reps'] == 30
