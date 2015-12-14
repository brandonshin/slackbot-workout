from bot.bot import Bot
from logger.loggers import PostgresDatabaseLogger
from util.configurators import EnvironmentTokenProvider, JsonFileConfigurationProvider
import time
import os

def main():
    logger = PostgresDatabaseLogger('flexecution', 'flexecution')
    configuration = JsonFileConfigurationProvider(os.getcwd() + '/config.json')
    tokens = EnvironmentTokenProvider()
    bot = Bot(logger, configuration, tokens)

    try:
        while True:
            if bot.isOfficeHours():
                # Re-fetch config file if settings have changed
                bot.loadConfiguration()

                # Get an exercise to do
                exercise = bot.selectExerciseAndStartTime()

                # Assign the exercise to someone
                bot.assignExercise(exercise)

            else:
                # Sleep the script and check again for office hours
                if not bot.debug:
                    time.sleep(5*60) # Sleep 5 minutes
                else:
                    # If debugging, check again in 5 seconds
                    time.sleep(5)

    except KeyboardInterrupt:
        bot.printStats()
        bot.saveUsers()


main()
