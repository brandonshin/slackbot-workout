import cherrypy
import logging
import threading
import time

from api import SlackbotApi
from bot import Bot, NoEligibleUsersException
from manager import UserManager
import util
from web import FlexbotWebServer

class Server(object):
    def __init__(self, workout_logger, configuration, tokens):
        self.logger = logging.getLogger(__name__)
        self.workout_logger = workout_logger
        self.configuration = configuration
        self.tokens = tokens
        self.slack_api = SlackbotApi(configuration, token=self.tokens.get_user_token())
        self.user_manager = UserManager(self.slack_api, self.configuration)
        self.bot = Bot(self.slack_api, self.workout_logger, self.configuration, self.user_manager)
        self.web_server = FlexbotWebServer(self.user_manager, configuration)

    def start(self):
        self.logger.debug('Starting workout loop')
        workout_loop_thread = threading.Thread(target=self.workout_loop)
        workout_loop_thread.daemon = False
        workout_loop_thread.start()
        # Start the webserver
        self.logger.debug('Starting webserver')
        cherrypy.config.update({'server.socket_host': '0.0.0.0',
                                'server.socket_port': self.configuration.webserver_port(),
                                'log.screen': True,
                               })
        cherrypy.quickstart(self.web_server)

    def workout_loop(self):
        was_office_hours = False

        while True:
            try:
                is_office_hours = self.bot.is_office_hours()
                if is_office_hours:
                    self.configuration.set_configuration()

                    # Get an exercise to do
                    exercise, mins_to_exercise = self.bot.select_exercise_and_start_time()
                    util.sleep(minutes=mins_to_exercise)

                    # Assign the exercise to someone
                    self.bot.assign_exercise(exercise)

                else:
                    if was_office_hours:
                        self.user_manager.stats()
                        self.user_manager.clear_users()
                    if not self.bot.debug:
                        util.sleep(minutes=5) # Sleep 5 minutes
                    else:
                        # If debugging, check again in 5 seconds
                        util.sleep(seconds=5)
                was_office_hours = is_office_hours

            except KeyboardInterrupt:
                self.logger.info("interrupted")
                self.configuration.set_configuration()
            except NoEligibleUsersException:
                time.sleep(5*60)
