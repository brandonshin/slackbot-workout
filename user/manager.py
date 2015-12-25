from user import User

class UserManager:
    def __init__(self, api, channel_name):
        self.api = api
        self.channel_id = self.api.fetch_channel_id(channel_name)
        self.users = {}

    def fetch_users(self):
        """
        Fetches a list of all active users in the channel
        """
        # Check for new members
        response = self.api.channels.info(self.channel_id).body
        user_ids = response['channel']['members']

        for user_id in user_ids:
            if user_id not in self.users:
                user_json = self.api.users.info(user_id).body['user']
                username = user_json['name']
                real_name = user_json['profile']['real_name']
                self.users[user_id] = User(user_id, username, real_name)

    def fetch_active_users(self):
        self.fetch_users()
        active_users = []
        for user_id in self.users:
            if self.is_active(user_id):
                active_users.append(self.users[user_id])
        return active_users

    def clear_users(self):
        self.users = {}

    def is_active(self, user_id):
        """
        Returns true if a user is currently "active", else false
        """
        response = self.api.users.get_presence(user_id).body
        return response['presence'] == "active"
