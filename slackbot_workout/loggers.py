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

class StdOutLogger(BaseLogger):
    def log_exercise(self, username, exercise, reps, units):
        print "%s %s %d %s" % (username, exercise, reps, units)

class CsvLogger(BaseLogger):
    def __init__(self, debug):
        self.debug = debug
        debugString = "_DEBUG" if debug else ""
        logfilename = "log" + time.strftime("%Y%m%d-%H%M")
        self.csv_filename = logfilename + debugString + ".csv" if debug else logfilename + ".csv"

    def log_exercise(self, username, exercise, reps, units):
        with open(self.csv_filename, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([str(datetime.datetime.now()),username,exercise,reps,units,self.debug])

class PostgresDatabaseLogger(BaseLogger):
    def __init__(self, dbname, tablename, **kwargs):
        self.debug = 'debug' in kwargs and kwargs['debug'] == True
        self.kwargs = kwargs
        self.kwargs.update({'dbname': dbname})
        self.tablename = tablename
        self.maybe_create_database()

    def with_connection(self, func):
        conn = None
        try:
            conn = psycopg2.connect(**self.kwargs)
            cursor = conn.cursor()
            if self.debug:
                print "precursor"
            func(cursor)
            conn.commit()
            if self.debug:
                print "committed"
        except psycopg2.Error as e:
            if self.debug:
                print e
            conn.rollback()
        finally:
            if conn:
                conn.close()

    def maybe_create_database(self):
        def create_database_command(cursor):
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS {} (
                    username VARCHAR(100),
                    exercise VARCHAR(100),
                    reps INT,
                    units VARCHAR(50),
                    time TIMESTAMP DEFAULT current_timestamp
                );
            """.format(self.tablename))
        self.with_connection(create_database_command)

    def log_exercise(self, username, exercise, reps, units):
        def log_exercise_command(cursor):
            cursor.execute("""
                INSERT INTO {}
                    (username, exercise, reps, units)
                VALUES
                    (%s, %s, %s, %s);
            """.format(self.tablename), (username, exercise, reps, units))
        self.with_connection(log_exercise_command)

