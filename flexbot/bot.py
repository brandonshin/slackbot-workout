import datetime
import logging
import random

from util import NoEligibleUsersException

# Configuration values to be set in setConfiguration
class Bot(object):
    def __init__(self, api, config, user_manager):
        self.api = api
        self.config = config
        self.user_manager = user_manager
        self.logger = logging.getLogger(__name__)


    def select_exercise_and_start_time(self):
        """
        Selects and announces to the channel an exercise and start time.
        """
        eligible_users = self.user_manager.get_eligible_users()
        return self._select_exercise_and_start_time(eligible_users)


    def _select_exercise_and_start_time(self, eligible_users):
        minute_interval = self.select_next_time_interval(eligible_users)
        self.logger.debug("Selected minute interval: %d", minute_interval)
        exercise = self.select_exercise()
        self.logger.debug("Selected exercise: %s", exercise.name)
        exercise_reps = random.randrange(exercise.min_reps, exercise.max_reps+1)
        self.logger.debug("Selected exercise reps: %s", exercise_reps)

        # Announcement String of next lottery time
        lottery_announcement = "NEXT LOTTERY FOR " + exercise.name.upper() + " IS IN " + str(minute_interval) + (" MINUTES" if minute_interval != 1 else " MINUTE")

        # Announce the exercise to the thread
        self.api.post_flex_message(lottery_announcement)

        return exercise, exercise_reps, minute_interval


    def select_exercise(self):
        """
        Selects the next exercise
        """
        exercises = self.config.exercises()
        idx = random.randrange(0, len(exercises))
        return exercises[idx]


    def select_next_time_interval(self, eligible_users):
        """
        Selects the next time interval
        """
        if self.config.office_hours_on():
            return self.select_next_time_interval_office_hours(eligible_users)
        else:
            return random.randint(self.config.min_time_between_callouts(),
                self.config.max_time_between_callouts())


    def select_next_time_interval_office_hours(self, eligible_users):
        # How much time is there left in the day
        time_left = datetime.datetime.now().replace(hour=self.config.office_hours_end(), minute=0,
                second=0, microsecond=0) - datetime.datetime.now()
        self.logger.debug("time_left (min): %d", time_left.seconds / 60)

        # How many exercises remain to be done
        exercise_count = sum(map(lambda u: self.user_manager.total_exercises_for_user(u),
            eligible_users))
        self.logger.debug("exercise_count: %d", exercise_count)

        max_exercises = self.config.user_exercise_limit() * len(eligible_users)
        self.logger.debug("max_exercises: %d", max_exercises)

        remaining_exercises = max_exercises - exercise_count
        self.logger.debug("remaining_exercises: %d", remaining_exercises)

        if remaining_exercises == 0:
            raise NoEligibleUsersException()

        # People called out per round
        num_online_users = len(eligible_users)
        self.logger.debug("num_online_users: %d", num_online_users)

        avg_people_per_callout = num_online_users * self.config.group_callout_chance() \
                + (self.num_people_in_current_callout(eligible_users)
                    * (1 - self.config.group_callout_chance()))
        self.logger.debug("avg_people_per_callout: %d", avg_people_per_callout)

        avg_minutes_per_exercise = time_left.seconds / float(remaining_exercises *
                avg_people_per_callout * 60)
        self.logger.debug("avg_minutes_per_exercise: %d", avg_minutes_per_exercise)

        return min(self.config.max_time_between_callouts(),
                   max(self.config.min_time_between_callouts(),
                       int(avg_minutes_per_exercise)))


    def assign_exercise(self, exercise, exercise_reps):
        """
        Selects a set of users or the channel to do the already-selected exercise, and returns the
        list of winners.
        """
        winner_announcement = "{} {} {} RIGHT NOW".format(exercise_reps, exercise.units, exercise.name)

        eligible_users = self.user_manager.get_eligible_users()
        winners = []

        # EVERYBODY
        if random.random() < self.config.group_callout_chance():
            winners = eligible_users
            winner_announcement += "<!channel>!"

        else:
            people_in_callout = self.num_people_in_current_callout(eligible_users)
            for i in range(people_in_callout):
                try:
                    winners.append(self.select_user(eligible_users, exercise))
                except:
                    break

            if len(winners) == 0:
                raise NoEligibleUsersException()

            for user in winners:
                winner_announcement += str(self.user_manager.get_mention(user))
                if i == len(winners) - 2:
                    winner_announcement += ", and "
                elif i == len(winners) - 1:
                    winner_announcement += "!"
                else:
                    winner_announcement += ", "

        for user in winners:
            self.user_manager.mark_winner(user, exercise, exercise_reps)

        # Announce the user
        self.api.post_flex_message(winner_announcement)

        return winners


    def select_user(self, eligible_users, exercise):
        """
        Selects an active user from the list of online users to complete the provided exercise
        """
        prime_users = filter(lambda u: not self.user_manager.user_has_done_exercise(u, exercise),
                eligible_users)
        # If there are users which haven't done the current exercise, assign the exercise to one of
        # them. Otherwise, assign it to any user.
        if len(prime_users) > 0:
            return self._select_user(exercise, prime_users)
        else:
            return self._select_user(exercise, eligible_users)


    def _select_user(self, exercise, user_list):
        """
        Chooses a user from the current list of eligible users.
        """
        lottery_list = self.get_lottery_list(user_list)
        return lottery_list[random.randint(0, len(lottery_list) - 1)]


    def get_lottery_list(self, user_list):
        lottery_list = []
        for user in user_list:
            exercises_done = self.user_manager.total_exercises_for_user(user)
            exercises_remaining = self.config.user_exercise_limit() - exercises_done
            lottery_list.extend([user] * exercises_remaining)
        return lottery_list


    def num_people_in_current_callout(self, active_users):
        return min(self.config.num_people_per_callout(), len(active_users))


    def is_office_hours(self):
        """
        Does the current time frame fall with the configured office hours?
        """
        if not self.config.office_hours_on():
            self.logger.debug("office hours disabled")
            return True
        now = datetime.datetime.now()
        now_time = now.time()
        is_weekday = now.weekday() < 5 # Monday - 0, ..., Sunday - 6
        office_hours_start = datetime.time(self.config.office_hours_begin())
        office_hours_end = datetime.time(self.config.office_hours_end())
        if office_hours_start <= now_time <= office_hours_end and is_weekday:
            self.logger.debug("in office hours")
            return True
        else:
            self.logger.debug("out office hours")
            return False
