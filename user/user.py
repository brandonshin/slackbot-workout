class User:
    def __init__(self, user_id, username, real_name):
        # The Slack ID of the user
        self.id = user_id

        # The username (@username) and real name
        self.username = username
        self.real_name = real_name

        # Exercise history for the day
        self.exercises = {}

        # User's online status
        self.online = False

    def get_user_handle(self):
        return ("@" + self.username).encode('utf-8')

    def add_exercise(self, exercise_id, reps):
        # Add to total counts
        try:
            current_sets, current_reps = self.exercises[exercise_id]
            self.exercises[exercise_id] = (current_sets + 1, current_reps + reps)
        except:
            self.exercises[exercise_id] = (1, reps)

    def total_exercises(self):
        total = 0
        for exercise_id in self.exercises:
            total += self.exercises[exercise_id][0]
        return total

    def get_exercise_count(self, exercise_id):
        try:
            return self.exercises[exercise_id][0]
        except:
            return 0

    def has_done_exercise(self, exercise_id):
        return exercise_id in self.exercises
