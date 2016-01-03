import datetime
import logging
import random

class NoEligibleUsersException(Exception):
    def __str__(self):
        return "No available users at this time"


# Configuration values to be set in setConfiguration
class Bot(object):
    def __init__(self, api, workout_logger, configurator, user_manager):
        self.api = api
        self.workout_logger = workout_logger
        self.configurator = configurator
        self.user_manager = user_manager
        self.logger = logging.getLogger(__name__)

        self.load_configuration()

        # round robin store
        self.user_queue = []


    def load_configuration(self):
        """
        Sets the configuration file.

        Runs after every callout so that settings can be changed realtime
        """
        # Read variables from the configurator
        settings = self.configurator.get_configuration()
        self.min_countdown = settings["callouts"]["timeBetween"]["minTime"]
        self.max_countdown = settings["callouts"]["timeBetween"]["maxTime"]
        self.num_people_per_callout = settings["callouts"]["numPeople"]
        self.group_callout_chance = settings["callouts"]["groupCalloutChance"]
        self.exercises = settings["exercises"]
        self.office_hours_on = settings["officeHours"]["on"]
        self.office_hours_begin = settings["officeHours"]["begin"]
        self.office_hours_end = settings["officeHours"]["end"]
        self.debug = settings["debug"]
        self.user_exercise_limit = settings["user_exercise_limit"]


    def update_user_queue(self):
        """
        Update our internal user queue from the user user_manager
        """
        active_users = self.user_manager.fetch_active_users()

        # Add all active users not already in the user queue
        # Shuffles to randomly add new active users
        random.shuffle(active_users)
        new_users = set(active_users) - set(self.user_queue)
        self.user_queue.extend(list(new_users))


    def get_eligible_users(self):
        """
        Get the current eligible users; throws NoEligibleUsersException if there are none. These are
        users who are online and have not yet completed their maximum daily limit of exercises.
        """
        self.update_user_queue()

        eligible_users = filter(lambda u: u.total_exercises() < self.user_exercise_limit, self.user_queue)
        if len(eligible_users) == 0:
            raise NoEligibleUsersException()

        return eligible_users


    def select_user(self, exercise):
        """
        Selects an active user from a list of users
        """
        eligible_users = self.get_eligible_users()
        num_eligible_users = len(eligible_users)

        # find a user to draw, priority going to first in
        for i in range(num_eligible_users):
            user = self.user_queue[i]

            # User should be active and not have done exercise yet
            if user in eligible_users and not user.has_done_exercise(exercise['id']):
                self.user_queue.remove(user)
                return user

        # Everyone has done this exercise, so pick an eligible user at random
        return eligible_users[random.randint(0, num_eligible_users - 1)]


    def select_exercise_and_start_time(self):
        """
        Selects and announces to the channel an exercise and start time.
        """
        eligible_users = self.get_eligible_users()
        return self._select_exercise_and_start_time(eligible_users)


    def _select_exercise_and_start_time(self, eligible_users):
        minute_interval = self.select_next_time_interval(eligible_users)
        exercise = self.select_exercise()

        # Announcement String of next lottery time
        lottery_announcement = "NEXT LOTTERY FOR " + exercise["name"].upper() + " IS IN " + str(minute_interval) + (" MINUTES" if minute_interval != 1 else " MINUTE")

        # Announce the exercise to the thread
        self.api.post_flex_message(lottery_announcement)

        return exercise, minute_interval


    def select_exercise(self):
        """
        Selects the next exercise
        """
        idx = random.randrange(0, len(self.exercises))
        return self.exercises[idx]


    def select_next_time_interval(self, eligible_users):
        """
        Selects the next time interval
        """
        # How much time is there left in the day
        time_left = datetime.datetime.now().replace(hour=self.office_hours_end, minute=0,
                second=0, microsecond=0) - datetime.datetime.now()
        self.logger.debug("time_left (min): %d", time_left.seconds / 60)

        # How many exercises remain to be done
        exercise_count = sum(map(lambda u: u.total_exercises(), eligible_users))
        self.logger.debug("exercise_count: %d", exercise_count)

        max_exercises = self.user_exercise_limit * len(eligible_users)
        self.logger.debug("max_exercises: %d", max_exercises)

        remaining_exercises = max_exercises - exercise_count
        self.logger.debug("remaining_exercises: %d", remaining_exercises)

        if remaining_exercises == 0:
            raise NoEligibleUsersException()

        # People called out per round
        num_online_users = len(eligible_users)
        self.logger.debug("num_online_users: %d", num_online_users)

        avg_people_per_callout = num_online_users * self.group_callout_chance \
                + self.num_people_in_current_callout() * (1 - self.group_callout_chance)
        self.logger.debug("avg_people_per_callout: %d", avg_people_per_callout)

        avg_minutes_per_exercise = time_left.seconds / float(remaining_exercises *
                avg_people_per_callout * 60)
        self.logger.debug("avg_minutes_per_exercise: %d", avg_minutes_per_exercise)

        if avg_minutes_per_exercise <= self.min_countdown:
            return self.min_countdown
        elif avg_minutes_per_exercise >= self.max_countdown:
            return self.max_countdown
        else:
            return int(avg_minutes_per_exercise)


    def assign_exercise(self, exercise):
        """
        Selects a person to do the already-selected exercise
        """
        # Select number of reps
        exercise_reps = random.randrange(exercise["minReps"], exercise["maxReps"]+1)

        winner_announcement = str(exercise_reps) + " " + str(exercise["units"]) + " " + exercise["name"] + " RIGHT NOW "

        eligible_users = self.get_eligible_users()

        # EVERYBODY
        if random.random() < self.group_callout_chance:
            winner_announcement += "@channel!"

            # Populate the user_cache
            for user in eligible_users:
                user.add_exercise(exercise['id'], exercise_reps)
                self.workout_logger.log_exercise(user.get_user_handle(),exercise["name"],exercise_reps,exercise["units"])

        else:
            winners = []
            people_in_callout = self.num_people_in_current_callout()
            for i in range(people_in_callout):
                try:
                    winners.append(self.select_user(exercise))
                except:
                    break

            if len(winners) == 0:
                raise NoEligibleUsersException()

            for user in winners:
                winner_announcement += str(user.get_user_handle())
                if i == len(winners) - 2:
                    winner_announcement += ", and "
                elif i == len(winners) - 1:
                    winner_announcement += "!"
                else:
                    winner_announcement += ", "

                user.add_exercise(exercise['id'], exercise_reps)
                self.workout_logger.log_exercise(user.get_user_handle(),exercise["name"],exercise_reps,exercise["units"])

        # Announce the user
        self.api.post_flex_message(winner_announcement)


    def num_people_in_current_callout(self):
        return min(self.num_people_per_callout, len(self.user_queue))


    def is_office_hours(self):
        """
        Does the current time frame fall with the configured office hours?
        """
        if not self.office_hours_on:
            self.logger.debug("not office hours")
            return True
        now = datetime.datetime.now()
        now_time = now.time()
        is_weekday = now.weekday() < 5 # Monday - 0, ..., Sunday - 6
        if datetime.time(self.office_hours_begin) <= now_time <= datetime.time(self.office_hours_end) and is_weekday:
            self.logger.debug("in office hours")
            return True
        else:
            self.logger.debug("out office hours")
            return False
