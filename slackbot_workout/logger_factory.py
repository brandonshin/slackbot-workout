from constants import Constants
import loggers

class LoggerFactory(object):
    def __init__(self, configuration):
        self.configuration = configuration

    def get_logger(self):
        logger_type = self.configuration.workout_logger_type()
        if logger_type == Constants.IN_MEMORY_LOGGER:
            return self.get_in_memory_logger()
        elif logger_type == Constants.CSV_LOGGER:
            return self.get_csv_logger()
        elif logger_type == Constants.POSTGRES_DATABASE_LOGGER:
            return self.get_postgres_database_logger()
        else:
            raise Exception("Unsupported logger type {}".format(logger_type))

    def get_in_memory_logger(self):
        return loggers.InMemoryLogger()

    def get_csv_logger(self):
        return loggers.CsvLogger(debug=self.configuration.debug())

    def get_postgres_database_logger(self):
        dbsettings = {}
        for setting in self.configuration.workout_logger_settings():
            dbsettings.update(setting)
        tablename = dbsettings['tablename']
        del dbsettings['tablename']
        return loggers.PostgresDatabaseLogger(tablename, **dbsettings)
