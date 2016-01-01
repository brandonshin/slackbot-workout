from slackbot_workout.loggers import PostgresDatabaseLogger, PostgresConnector

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
        logger = PostgresDatabaseLogger(self.dbname, self.tablename)
        logger.log_exercise('miles', 'pushups', 30, 'reps')

        def get_exercises(cursor):
            cursor.execute("SELECT username, exercise, reps FROM {}".format(self.tablename))
            return cursor.fetchall()
        exercises = self.with_connection(get_exercises)
        assert exercises == [('miles', 'pushups', 30)]

    def test_get_todays_exercises(self):
        logger = PostgresDatabaseLogger(self.dbname, self.tablename)
        logger.log_exercise('miles', 'pushups', 30, 'reps')
        logger.log_exercise('greg', 'situps', 40, 'reps')

        exercises = logger.get_todays_exercises()

        assert 'miles' in exercises
        assert exercises['miles'] == [{'exercise': 'pushups', 'reps': 30}]
        assert 'greg' in exercises
        assert exercises['greg'] == [{'exercise': 'situps', 'reps': 40}]
