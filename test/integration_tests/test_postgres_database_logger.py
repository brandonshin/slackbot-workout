from flexbot.exercise import Exercise
from flexbot.loggers import PostgresDatabaseLogger, PostgresConnector

exercises = [
    Exercise('pushups', 30, 40, 'reps', ''),
    Exercise('situps', 30, 40, 'reps', '')
]

class TestPostgresDatabaseLogger(PostgresConnector):
    dbname = 'travis_ci_test' # must be kept in sync with .travis.yml
    tablename = 'flexecution'
    kwargs = {'dbname': dbname}
    debug = False

    def teardown(self):
        def clear_table(cursor):
            cursor.execute("DELETE FROM {}".format(self.tablename))
        self.with_connection(clear_table)

    def test_log_exercise(self):
        logger = PostgresDatabaseLogger(self.tablename, dbname=self.dbname)
        logger.log_exercise('miles', exercises[0], 30)

        def get_exercises(cursor):
            cursor.execute("SELECT user_id, exercise, reps FROM {}".format(self.tablename))
            return cursor.fetchall()
        logged_exercises = self.with_connection(get_exercises)
        assert logged_exercises == [('miles', 'pushups', 30)]

    def test_get_todays_exercises(self):
        logger = PostgresDatabaseLogger(self.tablename, dbname=self.dbname)
        logger.log_exercise('miles', exercises[0], 30)
        logger.log_exercise('greg', exercises[1], 40)

        todays_exercises = logger.get_todays_exercises()

        assert 'miles' in todays_exercises
        assert todays_exercises['miles'] == [{'exercise': 'pushups', 'reps': 30}]
        assert 'greg' in todays_exercises
        assert todays_exercises['greg'] == [{'exercise': 'situps', 'reps': 40}]
