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

    @abstractmethod
    def log_exercise(self, user_id, exercise, reps):
        pass

    @abstractmethod
    def get_todays_exercises(self):
        pass

    # --------------------------------
    # Acknowledged mode logging api
    # --------------------------------

    @abstractmethod
    def get_current_winners(self):
        """
        Returns a hash of the current winners and the exercises assigned to them.
        """
        pass

    @abstractmethod
    def add_exercise(self, winner_id, exercise, reps):
        """
        Adds the provided exercise and reps to the given user.
        """
        pass

    @abstractmethod
    def finish_exercise(self, winner_id):
        """
        Removes the most recent exercise from the given winner with id winner_id, returning the
        exercise name and reps in a hash.
        """
        pass

class InMemoryLogger(BaseLogger):
    def __init__(self):
        super(InMemoryLogger, self).__init__()
        self.exercises = []
        self.winners = {}

    def log_exercise(self, user_id, exercise, reps):
        self.exercises.append((user_id, exercise, reps, datetime.datetime.now()))

    def get_todays_exercises(self):
        return filter(lambda log: log[3].date() == datetime.date.today(), self.exercises)

    def get_current_winners(self):
        return self.winners

    def add_exercise(self, winner_id, exercise, reps):
        exercise_entry = {
            'exercise': exercise,
            'reps': reps
        }
        try:
            self.winners[winner_id].append(exercise_entry)
        except:
            self.winners[winner_id] = [exercise_entry]

    def finish_exercise(self, winner_id):
        return self.winners[winner_id].pop(0)

class CsvLogger(BaseLogger):
    format_string = "%Y%m%d"

    def __init__(self):
        super(CsvLogger, self).__init__()

    def csv_filename(self):
        return "log" + time.strftime(self.format_string) + ".csv"

    def winners_filename(self):
        return "winners.csv"

    def log_exercise(self, user_id, exercise, reps):
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

    def get_current_winners(self):
        winners = {}
        with open(self.winners_filename(), 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                winner_id = row[0]
                exercise_data = {
                    'exercise': row[1],
                    'reps': int(row[2])
                }
                try:
                    winners[winner_id].append(exercise_data)
                except:
                    winners[winner_id] = [exercise_data]
        return winners

    def add_exercise(self, winner_id, exercise, reps):
        with open(self.winners_filename(), 'a') as f:
            writer = csv.writer(f)
            writer.writerow([winner_id, exercise.name, reps])

    def finish_exercise(self, winner_id):
        winners = self.get_current_winners()
        # Remove the finished exercise, and rewrite the winners csv
        exercise_data = winners[winner_id].pop(0)
        with open(self.winners_filename(), 'w') as f:
            writer = csv.writer(f)
            for winner_id in winners:
                for exercise in winners[winner_id]:
                    writer.writerow([winner_id, exercise['exercise'], exercise['reps']])
        return exercise_data


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
    def __init__(self, tablename, winners_table, **kwargs):
        super(PostgresDatabaseLogger, self).__init__()
        self.kwargs = kwargs
        self.tablename = tablename
        self.winners_table = winners_table
        self.maybe_create_tables()

    def maybe_create_tables(self):
        def create_tables_command(cursor):
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS {} (
                    user_id VARCHAR(100) NOT NULL,
                    exercise VARCHAR(100) NOT NULL,
                    reps INT NOT NULL,
                    units VARCHAR(50) NOT NULL,
                    time TIMESTAMP DEFAULT current_timestamp
                );
            """.format(self.tablename))
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS {} (
                    winner_id VARCHAR(100) NOT NULL,
                    exercise VARCHAR(100) NOT NULL,
                    reps INT NOT NULL,
                    time TIMESTAMP DEFAULT current_timestamp
                );
            """.format(self.winners_table))
        self.with_connection(create_tables_command)

    def log_exercise(self, user_id, exercise, reps):
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

    def get_current_winners(self):
        def get_current_winners_command(cursor):
            cursor.execute("""
                SELECT winner_id, exercise, reps FROM {} ORDER BY time ASC
            """.format(self.winners_table))
            exercises = {}
            for row in cursor.fetchall():
                winner_id = row[0]
                exercise_data = {
                    'exercise': row[1],
                    'reps': row[2]
                }
                try:
                    exercises[winner_id].append(exercise_data)
                except:
                    exercises[winner_id] = [exercise_data]
            return exercises
        return self.with_connection(get_current_winners_command)

    def add_exercise(self, winner_id, exercise, reps):
        def add_exercise_command(cursor):
            cursor.execute("""
                INSERT INTO {} (winner_id, exercise, reps) VALUES (%s, %s, %s)
            """.format(self.winners_table), (winner_id, exercise.name, reps))
        return self.with_connection(add_exercise_command)

    def finish_exercise(self, winner_id):
        def finish_exercise_command(cursor):
            cursor.execute("""
                DELETE FROM {} WHERE winner_id = %s AND time IN
                    (SELECT time FROM {} WHERE winner_id = %s ORDER BY time ASC LIMIT 1)
            """.format(self.winners_table, self.winners_table), (winner_id, winner_id))
        return self.with_connection(finish_exercise_command)
