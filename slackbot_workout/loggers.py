from abc import ABCMeta, abstractmethod
import csv
import datetime
import logging
import psycopg2
import time

class BaseLogger(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def log_exercise(self, user_id, exercise, reps):
        self.logger.debug("User {} completed {} {} of {}".format(user_id, reps, exercise.units,
            exercise.name))
        self._log_exercise(user_id, exercise, reps)

    @abstractmethod
    def _log_exercise(self, user_id, exercise, reps):
        pass

    @abstractmethod
    def get_todays_exercises(self):
        pass

class InMemoryLogger(BaseLogger):
    def __init__(self):
        super(InMemoryLogger, self).__init__()
        self.exercises = []

    def _log_exercise(self, user_id, exercise, reps):
        self.exercises.append((user_id, exercise, reps, datetime.datetime.now()))

    def get_todays_exercises(self):
        return filter(lambda log: log[3].date() == datetime.date.today(), self.exercises)

class CsvLogger(BaseLogger):
    format_string = "%Y%m%d"

    def __init__(self, debug=False):
        super(CsvLogger, self).__init__()
        self.debug = debug

    def csv_filename(self):
        debugString = "_DEBUG" if self.debug else ""
        return "log" + time.strftime(self.format_string) + debugString + ".csv"

    def _log_exercise(self, user_id, exercise, reps):
        with open(self.csv_filename(), 'a') as f:
            writer = csv.writer(f)
            now = str(datetime.datetime.now())
            writer.writerow([now, user_id, exercise.name, reps, exercise.units])

    def get_todays_exercises(self):
        exercises = {}
        with open(self.csv_filename(), 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                username = row[1]
                exercise_data = {
                    'exercise': row[2],
                    'reps': int(row[3])
                }
                try:
                    exercises[username].append(exercise_data)
                except:
                    exercises[username] = [exercise_data]
        return exercises

class PostgresConnector(object):
    def with_connection(self, func):
        conn = None
        try:
            conn = psycopg2.connect(**self.kwargs)
            cursor = conn.cursor()
            result = func(cursor)
            conn.commit()
            return result
        except psycopg2.Error:
            self.logger.exception("Failure during database connection")
            conn.rollback()
        finally:
            if conn:
                conn.close()

class PostgresDatabaseLogger(BaseLogger, PostgresConnector):
    def __init__(self, tablename, **kwargs):
        super(PostgresDatabaseLogger, self).__init__()
        self.debug = 'debug' in kwargs and kwargs['debug'] == True
        self.kwargs = kwargs
        self.tablename = tablename
        self.maybe_create_table()

    def maybe_create_table(self):
        def create_table_command(cursor):
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS {} (
                    user_id VARCHAR(100) NOT NULL,
                    exercise VARCHAR(100) NOT NULL,
                    reps INT NOT NULL,
                    units VARCHAR(50) NOT NULL,
                    time TIMESTAMP DEFAULT current_timestamp
                );
            """.format(self.tablename))
        self.with_connection(create_table_command)

    def _log_exercise(self, user_id, exercise, reps):
        def log_exercise_command(cursor):
            cursor.execute("""
                INSERT INTO {}
                    (user_id, exercise, reps, units)
                VALUES
                    (%s, %s, %s, %s);
            """.format(self.tablename), (user_id, exercise.name, reps, exercise.units))
        self.with_connection(log_exercise_command)

    def get_todays_exercises(self):
        def get_todays_exercises_command(cursor):
            cursor.execute("""
                SELECT user_id, exercise, reps
                FROM {}
                WHERE date_trunc('day', time) = date_trunc('day', now())
            """.format(self.tablename))
            exercises = {}
            for row in cursor.fetchall():
                user_id = row[0]
                exercise_data = {
                    'exercise': row[1],
                    'reps': row[2]
                }
                try:
                    exercises[user_id].append(exercise_data)
                except:
                    exercises[user_id] = [exercise_data]
            return exercises

        return self.with_connection(get_todays_exercises_command)
