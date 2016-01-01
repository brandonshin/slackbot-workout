import time
import csv
import datetime
from abc import ABCMeta, abstractmethod
import psycopg2

class BaseLogger:
    __metaclass__ = ABCMeta

    @abstractmethod
    def log_exercise(self, username, exercise, reps, units):
        pass

    @abstractmethod
    def get_todays_exercises(self):
        pass

class StdOutLogger(BaseLogger):
    def log_exercise(self, username, exercise, reps, units):
        print "%s %s %d %s" % (username, exercise, reps, units)

    def get_todays_exercises(self):
        # We aren't actually persisting this data, so return no exercises for anyone
        return {}

class CsvLogger(BaseLogger):
    format_string = "%Y%m%d"

    def __init__(self, debug=False):
        self.debug = debug

    def csv_filename(self):
        debugString = "_DEBUG" if self.debug else ""
        return "log" + time.strftime(self.format_string) + debugString + ".csv"

    def log_exercise(self, username, exercise, reps, units):
        with open(self.csv_filename(), 'a') as f:
            writer = csv.writer(f)
            writer.writerow([str(datetime.datetime.now()),username,exercise,reps,units])

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

class PostgresConnector:
    def with_connection(self, func):
        conn = None
        try:
            conn = psycopg2.connect(**self.kwargs)
            cursor = conn.cursor()
            if self.debug:
                print "precursor"
            result = func(cursor)
            conn.commit()
            if self.debug:
                print "committed"
            return result
        except psycopg2.Error as e:
            if self.debug:
                print e
            conn.rollback()
        finally:
            if conn:
                conn.close()

class PostgresDatabaseLogger(BaseLogger, PostgresConnector):
    def __init__(self, dbname, tablename, **kwargs):
        self.debug = 'debug' in kwargs and kwargs['debug'] == True
        self.kwargs = kwargs
        self.kwargs.update({'dbname': dbname})
        self.tablename = tablename
        self.maybe_create_table()

    def maybe_create_table(self):
        def create_table_command(cursor):
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS {} (
                    username VARCHAR(100),
                    exercise VARCHAR(100),
                    reps INT,
                    units VARCHAR(50),
                    time TIMESTAMP DEFAULT current_timestamp
                );
            """.format(self.tablename))
        self.with_connection(create_table_command)

    def log_exercise(self, username, exercise, reps, units):
        def log_exercise_command(cursor):
            cursor.execute("""
                INSERT INTO {}
                    (username, exercise, reps, units)
                VALUES
                    (%s, %s, %s, %s);
            """.format(self.tablename), (username, exercise, reps, units))
        self.with_connection(log_exercise_command)

    def get_todays_exercises(self):
        def get_todays_exercises_command(cursor):
            cursor.execute("""
                SELECT username, exercise, reps
                FROM {}
                WHERE date_trunc('day', time) = date_trunc('day', now())
            """.format(self.tablename))
            exercises = {}
            for row in cursor.fetchall():
                username = row[0]
                exercise_data = {
                    'exercise': row[1],
                    'reps': row[2]
                }
                try:
                    exercises[username].append(exercise_data)
                except:
                    exercises[username] = [exercise_data]
            return exercises

        return self.with_connection(get_todays_exercises_command)
