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
    def __init__(self, dbhost, dbport, dbname, username, password):
        self.dbname = dbname
        self.dbhost = dbhost
        self.dbport = dbport
        self.username = username
        self.password = password
        self.maybeCreateDatabase()

    def withConnection(self, func):
        conn = None
        try:
            conn = psycopg2.connect(database=self.dbname, host=self.dbhost, port=self.dbport,
                    user=self.username, password=self.password)
            cursor = conn.cursor()
            func(cursor)
            conn.commit()
        except psycopg2.PostgresException:
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
                    time TIMESTAMP
                )
            """.format(self.dbname))
        self.withConnection(createDatabaseCommand)

    def logExercise(self, username, exercise, reps, units, debug):
        def logExerciseCommand(cursor):
            cursor.execute("""
                INSERT INTO {}
                    (username, exercise, reps, units, time)
                VALUES
                    (%s, %s, %d, %s, current_timestamp())
            """, (username, exercise, reps, units))
        self.withConnection(logExerciseCommand)

