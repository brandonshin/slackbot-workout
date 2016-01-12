import json
import logging

from user import User

class UserManager(object):
    def __init__(self, api, configuration):
        self.api = api
        self.configuration = configuration
        self.logger = logging.getLogger(__name__)
        self.users = {}
        self.current_winners = []
        self.fetch_users()

    def stats(self, user_id_list=[]):
        # Write to the command console today's breakdown
        s = "```\n"
        #s += "Username\tAssigned\tComplete\tPercent
        s += "Username".ljust(15)
        exercises = self.configuration.exercises()
        for exercise in exercises:
            s += exercise.name + "  "
        s += "\n---------------------------------------------------------------\n"

        user_ids = user_id_list if len(user_id_list) > 0 else self.users.keys()
        for user_id in user_ids:
            user = self.users[user_id]
            s += user.username.ljust(15)
            for exercise in exercises:
                s += str(user.get_exercise_count(exercise.name)).ljust(len(exercise.name) + 2)
            s += "\n"

        s += "```"
        return s

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
                active_users.append(self.users[user_id])
        return active_users

    def clear_users(self):
        self.users = {}

    def add_to_current_winners(self, user_id, exercise, reps):
        self.current_winners.append((user_id, exercise, reps))

    def get_current_winners(self):
        return self.current_winners

    def remove_from_current_winners(self, user_id):
        self.current_winners = filter(lambda u: u[0] != user_id, self.current_winners)

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
