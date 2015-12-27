from bot.bot import Bot, NoEligibleUsersException
from user.manager import UserManager
from client.api import SlackbotApi
from web import FlexbotWebServer
import time
import threading
import cherrypy

class Server:
    def __init__(self, logger, configuration, tokens):
        self.logger = logger
        self.configuration = configuration
        self.tokens = tokens
        self.slack_api = SlackbotApi(configuration, token=self.tokens.get_user_token())
        self.user_manager = UserManager(self.slack_api, self.configuration)
        self.bot = Bot(self.slack_api, self.logger, self.configuration, self.user_manager)
        self.web_server = FlexbotWebServer(self.user_manager, configuration)

    def start(self):
        workout_loop_thread = threading.Thread(target=self.workout_loop)
        workout_loop_thread.daemon = False
        workout_loop_thread.start()
        # Start the webserver
        cherrypy.config.update({'server.socket_host': '0.0.0.0',
                                'server.socket_port': 80,
                                'log.screen': True,
                               })
        cherrypy.quickstart(self.web_server)

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
                        self.user_manager.stats()
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

