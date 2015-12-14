import time
import csv
import datetime
from abc import ABCMeta, abstractmethod
import psycopg2

class BaseLogger:
    __metaclass__ = ABCMeta

    @abstractmethod
    def logExercise(self, time, username, exercise, reps, units):
        pass

class CsvLogger(BaseLogger):
    def __init__(self, debug):
        debugString = "_DEBUG" if debug else ""
        logfilename = "log" + time.strftime("%Y%m%d-%H%M")
        self.csv_filename = logfilename + debugString + ".csv" if debug else logfilename + ".csv"

    def logExercise(self, username, exercise, reps, units, debug):
        with open(self.csv_filename, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([str(datetime.datetime.now()),username,exercise,reps,units,debug])

class PostgresDatabaseLogger(BaseLogger):
    def __init__(self, dbname, tablename, **kwargs):
        self.kwargs = kwargs
        self.kwargs.update({'dbname': dbname})
        self.tablename = tablename
        self.maybeCreateDatabase()

    def withConnection(self, func, debug=False):
        conn = None
        try:
            conn = psycopg2.connect(**self.kwargs)
            cursor = conn.cursor()
            if debug:
                print "precursor"
            func(cursor)
            conn.commit()
            if debug:
                print "committed"
        except psycopg2.Error as e:
            if debug:
                print e
            conn.rollback()
        finally:
            if conn:
                conn.close()

    def maybeCreateDatabase(self):
        def createDatabaseCommand(cursor):
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS {} (
                    username VARCHAR(100),
                    exercise VARCHAR(100),
                    reps INT,
                    units VARCHAR(50),
                    time TIMESTAMP DEFAULT current_timestamp
                );
            """.format(self.tablename))
        self.withConnection(createDatabaseCommand)

    def logExercise(self, username, exercise, reps, units, debug):
        def logExerciseCommand(cursor):
            cursor.execute("""
                INSERT INTO {}
                    (username, exercise, reps, units)
                VALUES
                    (%s, %s, %s, %s);
            """.format(self.tablename), (username, exercise, reps, units))
        self.withConnection(logExerciseCommand, debug=debug)

