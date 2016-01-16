class User(object):
    def __init__(self, user_id, username, firstname, lastname):
        # The Slack ID of the user
        self.id = user_id

        # The username (@username) and real name
        self.username = username
        self.firstname = firstname
        self.lastname = lastname

    def __str__(self):
        return self.get_user_handle()

    def get_user_handle(self):
        return ("@" + self.username).encode('utf-8')

    def get_mention(self):
        return "<" + self.get_user_handle() + ">"
