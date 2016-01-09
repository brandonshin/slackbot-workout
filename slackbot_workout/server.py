import cherrypy
import logging
import threading

from api import SlackbotApi
from bot import Bot, NoEligibleUsersException
from constants import Constants
from manager import UserManager
import util
from web import FlexbotWebServer

class Server(object):
    def __init__(self, workout_logger, configuration, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.workout_logger = workout_logger
        self.configuration = configuration
        self.current_winners = []

        if 'slack_api' in kwargs:
            self.slack_api = kwargs['slack_api']
        else:
            self.slack_api = SlackbotApi(configuration, token=self.configuration.slack_token())

        if 'user_manager' in kwargs:
            self.user_manager = kwargs['user_manager']
        else:
            self.user_manager = UserManager(self.slack_api, self.configuration)

        if 'bot' in kwargs:
            self.bot = kwargs['bot']
        else:
            self.bot = Bot(self.slack_api, self.workout_logger, self.configuration, self.user_manager)

        if 'web_server' in kwargs:
            self.web_server = kwargs['web_server']
        else:
            self.web_server = FlexbotWebServer(self.user_manager, self, configuration)

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
        """
        Runs the workout bot in an infinite loop.
        """
        was_office_hours = False

        while True:
            was_office_hours = self.workout_step(was_office_hours)

    def workout_step(self, was_office_hours):
        """
        Runs a step of the workout bot, handling exceptions. Returns True iff is_office_hours
        returns true before the current workout.
        """
        is_office_hours = self.bot.is_office_hours()
        try:
            self._workout_step(was_office_hours, is_office_hours)
        except NoEligibleUsersException:
            util.sleep(minutes=5)
        return is_office_hours

    def _workout_step(self, was_office_hours, is_office_hours):
        if is_office_hours:
            # Clear the previous day's history if this is the first workout of the day
            if not was_office_hours:
                self.user_manager.clear_users()

            # Get an exercise to do
            exercise, reps, mins_to_exercise = self.bot.select_exercise_and_start_time()
            util.sleep(minutes=mins_to_exercise)

            # Assign the exercise to someone
            self.current_winners = self.bot.assign_exercise(exercise, reps)
            self.current_exercise = exercise
            self.current_reps = reps
        else:
            # Show some stats if the final workout has just passed
            if was_office_hours:
                self.slack_api.post_flex_message(self.user_manager.stats())

            # Sleep for a bit
            if not self.configuration.debug():
                util.sleep(minutes=5) # Sleep 5 minutes
            else:
                # If debugging, check again in 5 seconds
                util.sleep(seconds=5)

    def acknowledge_winner(self, user_id):
        if self.configuration.enable_acknowledgment():
            try:
                user = filter(lambda u: u.id == user_id, self.current_winners)[0]
                exercise = self.current_exercise

                # Log the exercise, update the local user's information as well, and remove the user
                # from the list of current winners
                self.workout_logger.log_exercise(user.id, exercise, self.current_reps)
                self.user_manager.users[user.id].add_exercise(exercise.id, self.current_reps)
                self.current_winners.remove(user)
                return Constants.ACKNOWLEDGE_SUCCEEDED
            except IndexError: # user not actually in the list of current winners
                return Constants.ACKNOWLEDGE_FAILED
        else:
            return Constants.ACKNOWLEDGE_DISABLED
