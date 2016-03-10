import psycopg2

class DB:
    def __init__(self, table_name):
        self.table_name = table_name
        self.connect()

    def __del__(self):
        print "Closing connections"
        self.cursor().close()
        self.connection.close()

    def connect(self):
        database_name = "slackbotworkout"
        try:
            self.connection = psycopg2.connect(database=database_name)
        except psycopg2.OperationalError as oe:
            pg_connection = psycopg2.connect(database="postgres")
            pg_connection.set_isolation_level(0)
            pg_connection.cursor().execute("CREATE DATABASE " + database_name)
            pg_connection.cursor().close()
            pg_connection.close()
            self.connection = psycopg2.connect(database=database_name)
            self.connection.set_isolation_level(1)
            self.connection.cursor().execute("CREATE TABLE " + self.table_name + ""
                " ( "
                "    id serial PRIMARY KEY,"
                "    username varchar, "
                "    exercise varchar, "
                "    reps integer, "
                "    assigned_at timestamp, "
                "    completed_at timestamp"
                ");"
                )
            self.connection.commit()
            

    def cursor(self):
        return self.connection.cursor()

    def ensure_connected(self):
        try:
            self.connection.isolation_level
        except OperationalError as oe:
            self.connect()

    def assign(self, values):
        self.ensure_connected()
        add_row = (
            "INSERT INTO " + self.table_name + ""
            "(username, exercise, reps, assigned_at)"
            "VALUES (%(username)s, %(exercise)s, %(reps)s, %(assigned_at)s)"
        )
        self.cursor().execute(add_row, values)
        self.connection.commit()

    def complete(self, query):
        self.ensure_connected()
        update_row = (
            "UPDATE " + self.table_name + ""
            " SET completed_at = now()"
            "WHERE username = %(username)s AND exercise = %(exercise)s and assigned_at = %(assigned_at)s"
        )
        self.cursor().execute(update_row, values)
        self.connection.commit()
