import json
import logging

from constants import Constants
from user import User
from util import NoEligibleUsersException

class UserManager(object):
    def __init__(self, api, configuration, workout_logger):
        self.api = api
        self.configuration = configuration
        self.workout_logger = workout_logger
        self.logger = logging.getLogger(__name__)
        self.users = {}
        self.current_winners = {}
        self.fetch_users()

    def stats(self, user_id_list=[]):
        # Write to the command console today's breakdown
        s = "Today's stats:\n"
        s += "```\n"
        #s += "Username\tAssigned\tComplete\tPercent
        s += "Username".ljust(15)
        exercises = self.configuration.exercises()
        for exercise in exercises:
            s += exercise.name + "  "
        s += "Total\n"
        s += "---------------------------------------------------------------\n"

        user_ids = user_id_list if len(user_id_list) > 0 else self.users.keys()
        for user_id in user_ids:
            s += self.get_username(user_id).ljust(15)
            for exercise in exercises:
                s += str(self.exercise_count_for_user(user_id, exercise)).ljust(len(exercise.name) + 2)
            s += str(self.total_exercises_for_user(user_id))
            s += "\n"

        s += "```"
        return s

    # --------------------------------------
    # Fetching users from the channel
    # --------------------------------------

    def fetch_users(self):
        """
        Fetches all users in the channel
        """
        # Check for new members
        user_ids = self.api.get_members()

        for user_id in user_ids:
            if user_id not in self.users:
                user_json = self.api.get_user_info(user_id)
                self.logger.info("Adding user with json: %s", json.dumps(user_json))
                username = user_json['name']
                firstname = user_json['profile'].get('first_name', '')
                lastname = user_json['profile'].get('last_name', '')
                self.users[user_id] = User(user_id, username, firstname, lastname)

    def fetch_active_users(self):
        """
        Returns a list of all active users in the channel
        """
        self.fetch_users()
        active_users = []
        for user_id in self.users:
            if self.api.is_active(user_id):
                active_users.append(user_id)
        return active_users

    def clear_users(self):
        self.users = {}

    # --------------------------------------
    # Current winners
    # --------------------------------------

    def add_to_current_winners(self, user_id, exercise, reps):
        try:
            self.current_winners[user_id].append((exercise, reps))
        except:
            self.current_winners[user_id] = [(exercise, reps)]

    def get_current_winners(self):
        return self.current_winners

    def remove_from_current_winners(self, user_id):
        self.current_winners[user_id].pop(0)
        if len(self.current_winners[user_id]) == 0:
            del self.current_winners[user_id]

    def mark_winner(self, user_id, exercise, exercise_reps):
        if self.configuration.enable_acknowledgment():
            self.add_to_current_winners(user_id, exercise, exercise_reps)
        else:
            self.add_exercise_for_user(user_id, exercise, exercise_reps)

    def acknowledge_winner(self, user_id):
        if self.configuration.enable_acknowledgment():
            try:
                exercise, reps = self.current_winners[user_id][0]

                # Log the exercise, update the local user's information as well, and remove the user
                # from the list of current winners
                self.add_exercise_for_user(user_id, exercise, reps)
                self.remove_from_current_winners(user_id)
                return Constants.ACKNOWLEDGE_SUCCEEDED
            except IndexError: # user not actually in the list of current winners
                return Constants.ACKNOWLEDGE_FAILED
        else:
            return Constants.ACKNOWLEDGE_DISABLED

    # --------------------------------------
    # User utility methods
    # --------------------------------------

    def get_firstname(self, user_id):
        try:
            return self.users[user_id].firstname
        except KeyError:
            return None

    def get_username(self, user_id):
        try:
            return self.users[user_id].username
        except KeyError:
            return None

    def get_mention(self, user_id):
        try:
            return self.users[user_id].get_mention()
        except:
            return None

    # --------------------------------------
    # Exercise management
    # --------------------------------------

    def get_eligible_users(self):
        """
        Get the current eligible users; throws NoEligibleUsersException if there are none. These are
        users who are online and have not yet completed their maximum daily limit of exercises.
        """
        active_users = self.fetch_active_users()

        winner_ids = self.get_current_winners().keys()
        eligible_users = []
        for user_id in active_users:
            total_exercises = self.total_exercises_for_user(user_id)
            if user_id not in winner_ids and total_exercises < self.configuration.user_exercise_limit():
                self.logger.info("Adding %s to eligible_users list", self.get_username(user_id))
                eligible_users.append(user_id)

        if len(eligible_users) == 0:
            raise NoEligibleUsersException()

        return eligible_users

    def total_exercises_for_user(self, user_id):
        exercises = self.workout_logger.get_todays_exercises()
        try:
            return len(exercises[user_id])
        except KeyError:
            return 0

    def exercise_count_for_user(self, user_id, exercise):
        exercises = self.workout_logger.get_todays_exercises()
        try:
            filtered_exercises = filter(lambda e: e['exercise'] == exercise, exercises[user_id])
            return len(filtered_exercises)
        except KeyError:
            return 0

    def user_has_done_exercise(self, user_id, exercise):
        return self.exercise_count_for_user(user_id, exercise) > 0

    def add_exercise_for_user(self, user_id, exercise, exercise_reps):
        self.workout_logger.log_exercise(user_id, exercise, exercise_reps)

