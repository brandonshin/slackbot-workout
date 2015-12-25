from bot.bot import Bot, NoEligibleUsersException
from logger.loggers import CsvLogger
from user.manager import UserManager
from util.configurators import EnvironmentTokenProvider, JsonFileConfigurationProvider
from client.api import SlackbotApi
import time
import os
import threading

class Server:
    def __init__(self):
        self.logger = CsvLogger(False)
        self.configuration = JsonFileConfigurationProvider(os.getcwd() + '/config.json')
        self.tokens = EnvironmentTokenProvider()
        self.slack_api = SlackbotApi(token=self.tokens.get_user_token())
        self.user_manager = UserManager(self.slack_api, 'testflexecution2')
        self.bot = Bot(self.slack_api, self.logger, self.configuration, self.user_manager)

    def start(self):
        workout_loop_thread = threading.Thread(target=self.workout_loop)
        workout_loop_thread.daemon = False
        workout_loop_thread.start()

    def workout_loop(self):
        was_office_hours = False

        while True:
            try:
                is_office_hours = self.bot.is_office_hours()
                if is_office_hours:
                    # Re-fetch config file if settings have changed
                    self.bot.load_configuration()

                    # Get an exercise to do
                    exercise = self.bot.select_exercise_and_start_time()

                    # Assign the exercise to someone
                    self.bot.assign_exercise(exercise)

                else:
                    if was_office_hours:
                        self.bot.printStats()
                        self.user_manager.clear_users()
                    if not self.bot.debug:
                        time.sleep(5*60) # Sleep 5 minutes
                    else:
                        # If debugging, check again in 5 seconds
                        time.sleep(5)
                was_office_hours = is_office_hours

            except KeyboardInterrupt:
                print "interrupted"
            except NoEligibleUsersException:
                time.sleep(5*60)

