import time

def sleep(minutes=0, seconds=0):
    time.sleep(minutes * 60 + seconds)

class StatementRenderer(object):
    def __init__(self, format_string):
        self.format_string = format_string
        num_specifiers = format_string.count('{}')
        if num_specifiers == 0:
            self.needs_user = False
        elif num_specifiers == 1:
            self.needs_user = True
        else:
            raise Exception("Must have zero or one format specifiers")

    def render_statement(self, username):
        if self.needs_user:
            return self.format_string.format(username)
        else:
            return self.format_string

class InvalidLoggerTypeException(Exception):
    def __init__(self, logger_type):
        self.logger_type = logger_type

    def __str__(self):
        return "{} is not a valid logger type".format(self.logger_type)

class NoEligibleUsersException(Exception):
    def __str__(self):
        return "No available users at this time"

