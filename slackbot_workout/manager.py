from user import User

class UserManager(object):
    def __init__(self, api, configuration):
        self.api = api
        self.configuration = configuration
        self.users = {}
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
                s += str(user.get_exercise_count(exercise.id)).ljust(len(exercise.name) + 2)
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
                username = user_json['name']
                firstname = user_json['profile']['first_name']
                lastname = user_json['profile']['last_name']
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

    def get_firstname(self, user_id):
        try:
            return self.users[user_id].firstname
        except KeyError:
            return None
