import random
import time
import datetime
from random import shuffle

class NoEligibleUsersException(Exception):
    def __str__(self):
        return "No available users at this time"

# Configuration values to be set in setConfiguration
class Bot:
    def __init__(self, api, logger, configurator, user_manager):
        self.api = api
        self.logger = logger
        self.configurator = configurator
        self.user_manager = user_manager

        self.load_configuration()

        # round robin store
        self.user_queue = []

    '''
    Sets the configuration file.

    Runs after every callout so that settings can be changed realtime
    '''
    def load_configuration(self):
        # Read variables from the configurator
        settings = self.configurator.get_configuration()
        self.team_domain = settings["teamDomain"]
        self.channel_name = settings["channelName"]
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

    def select_user(self, exercise):
        """
        Selects an active user from a list of users
        """
        active_users = self.user_manager.fetch_active_users()

        # Add all active users not already in the user queue
        # Shuffles to randomly add new active users
        shuffle(active_users)
        new_users = set(active_users) - set(self.user_queue)
        self.user_queue.extend(list(new_users))
        eligible_users = filter(lambda u: u.total_exercises() <= self.user_exercise_limit,
                self.user_queue)
        num_eligible_users = len(eligible_users)

        if num_eligible_users == 0:
            raise NoEligibleUsersException()

        # find a user to draw, priority going to first in
        for i in range(num_eligible_users):
            user = self.user_queue[i]

            # User should be active and not have done exercise yet
            if user in active_users and not user.has_done_exercise(exercise['id']):
                self.user_queue.remove(user)
                return user

        # Everyone has done this exercise, so pick an eligible user at random
        return eligible_users[random.randint(0, num_eligible_users - 1)]

    def select_exercise_and_start_time(self):
        """
        Selects an exercise and start time, and sleeps until the time
        period has past.
        """
        minute_interval = self.select_next_time_interval()
        exercise = self.select_exercise()

        # Announcement String of next lottery time
        lottery_announcement = "NEXT LOTTERY FOR " + exercise["name"].upper() + " IS IN " + str(minute_interval) + (" MINUTES" if minute_interval != 1 else " MINUTE")

        # Announce the exercise to the thread
        self.api.post_flex_message(lottery_announcement)

        # Sleep the script until time is up
        if not self.debug:
            time.sleep(minute_interval * 60)
        else:
            # If debugging, once every 5 seconds
            time.sleep(5)

        return exercise


    '''
    Selects the next exercise
    '''
    def select_exercise(self):
        idx = random.randrange(0, len(self.exercises))
        return self.exercises[idx]


    '''
    Selects the next time interval
    '''
    def select_next_time_interval(self):
        # How much time is there left in the day
        time_left = datetime.datetime.now().replace(hour=self.office_hours_end, minute=0,
                second=0, microsecond=0) - datetime.datetime.now()
        self.debug_print("time_left (min): %d" % (time_left.seconds / 60))

        # How many exercises remain to be done
        exercise_count = sum(map(lambda u: u.total_exercises(),
            self.user_manager.fetch_active_users()))
        self.debug_print("exercise_count: %d" % exercise_count)
        max_exercises = self.user_exercise_limit * len(self.user_manager.users)
        self.debug_print("max_exercises: %d" % max_exercises)
        remaining_exercises = max_exercises - exercise_count
        self.debug_print("remaining_exercises: %d" % remaining_exercises)

        if remaining_exercises == 0:
            raise NoEligibleUsersException()

        # People called out per round
        num_online_users = len(self.user_manager.fetch_active_users())
        self.debug_print("num_online_users: %d" % num_online_users)
        avg_people_per_callout = num_online_users * self.group_callout_chance \
                + self.num_people_per_callout * (1 - self.group_callout_chance)
        self.debug_print("avg_people_per_callout: %d" % avg_people_per_callout)

        avg_minutes_per_exercise = time_left.seconds / float(remaining_exercises *
                avg_people_per_callout * 60)
        self.debug_print("avg_minutes_per_exercise: %d" % avg_minutes_per_exercise)

        if avg_minutes_per_exercise <= self.min_countdown:
            return self.min_countdown
        elif avg_minutes_per_exercise >= self.max_countdown:
            return self.max_countdown
        else:
            return avg_minutes_per_exercise


    '''
    Selects a person to do the already-selected exercise
    '''
    def assign_exercise(self, exercise):
        # Select number of reps
        exercise_reps = random.randrange(exercise["minReps"], exercise["maxReps"]+1)

        winner_announcement = str(exercise_reps) + " " + str(exercise["units"]) + " " + exercise["name"] + " RIGHT NOW "

        # EVERYBODY
        if random.random() < self.group_callout_chance:
            winner_announcement += "@channel!"

            # Populate the user_cache
            active_users = self.user_manager.fetch_active_users()
            for user in active_users:
                user.add_exercise(exercise['id'], exercise_reps)
                self.logger.log_exercise(user.get_user_handle(),exercise["name"],exercise_reps,exercise["units"])

        else:
            winners = []
            for i in range(self.num_people_per_callout):
                try:
                    winners.append(self.select_user(exercise))
                except:
                    break

            if len(winners) == 0:
                raise NoEligibleUsersException()

            for user in winners:
                winner_announcement += str(user.get_user_handle())
                if i == self.num_people_per_callout - 2:
                    winner_announcement += ", and "
                elif i == self.num_people_per_callout - 1:
                    winner_announcement += "!"
                else:
                    winner_announcement += ", "

                user.add_exercise(exercise['id'], exercise_reps)
                self.logger.log_exercise(user.get_user_handle(),exercise["name"],exercise_reps,exercise["units"])

        # Announce the user
        self.api.post_flex_message(winner_announcement)

    def is_office_hours(self):
        if not self.office_hours_on:
            self.debug_print("not office hours")
            return True
        now = datetime.datetime.now()
        now_time = now.time()
        is_weekday = now.weekday() < 5 # Monday - 0, ..., Sunday - 6
        if datetime.time(self.office_hours_begin) <= now_time <= datetime.time(self.office_hours_end) and is_weekday:
            self.debug_print("in office hours")
            return True
        else:
            self.debug_print("out office hours")
            return False

    def debug_print(self, msg):
        if self.debug:
            print msg
