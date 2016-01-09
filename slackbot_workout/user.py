class User(object):
    def __init__(self, user_id, username, firstname, lastname):
        # The Slack ID of the user
        self.id = user_id

        # The username (@username) and real name
        self.username = username
        self.firstname = firstname
        self.lastname = lastname

        # Exercise history for the day
        self.exercises = {}

        # User's online status
        self.online = False

    def __str__(self):
        return self.get_user_handle()

    def get_user_handle(self):
        return ("@" + self.username).encode('utf-8')

    def get_mention(self):
        return "<" + self.get_user_handle() + ">"

    def add_exercise(self, exercise_name, reps):
        if reps > 0:
            # Add to total counts
            try:
                current_sets, current_reps = self.exercises[exercise_name]
                self.exercises[exercise_name] = (current_sets + 1, current_reps + reps)
            except:
                self.exercises[exercise_name] = (1, reps)

    def total_exercises(self):
        total = 0
        for exercise_name in self.exercises:
            total += self.exercises[exercise_name][0]
        return total

    def get_exercise_count(self, exercise_name):
        try:
            return self.exercises[exercise_name][0]
        except:
            return 0

    def has_done_exercise(self, exercise_name):
        return exercise_name in self.exercises
