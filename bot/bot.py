import random
import time
import datetime
import requests
import json
import os
from random import shuffle
import pickle
import os.path

from user.user import User
from util.fetchChannelId import fetchChannelId

HASH = "%23"

# Configuration values to be set in setConfiguration
class Bot:
    def __init__(self, logger, configurator, tokens, shouldCache=False):
        self.configurator = configurator
        self.logger = logger
        self.shouldCache = shouldCache
        self.userToken = tokens.getUserToken()
        self.urlToken = tokens.getUrlToken()

        self.loadConfiguration()
        self.first_run = True

        # local cache of usernames
        # maps userIds to usernames
        self.user_cache = self.loadUserCache()

        # round robin store
        self.user_queue = []


    def loadUserCache(self):
        if self.shouldCache and os.path.isfile('user_cache.save'):
            with open('user_cache.save','rb') as f:
                self.user_cache = pickle.load(f)
                print "Loading " + str(len(self.user_cache)) + " users from cache."
                return self.user_cache

        return {}

    '''
    Sets the configuration file.

    Runs after every callout so that settings can be changed realtime
    '''
    def loadConfiguration(self):
        # Read variables from the configurator
        settings = self.configurator.getConfiguration()
        self.team_domain = settings["teamDomain"]
        self.channel_name = settings["channelName"]
        self.min_countdown = settings["callouts"]["timeBetween"]["minTime"]
        self.max_countdown = settings["callouts"]["timeBetween"]["maxTime"]
        self.num_people_per_callout = settings["callouts"]["numPeople"]
        self.sliding_window_size = settings["callouts"]["slidingWindowSize"]
        self.group_callout_chance = settings["callouts"]["groupCalloutChance"]
        self.exercises = settings["exercises"]
        self.office_hours_on = settings["officeHours"]["on"]
        self.office_hours_begin = settings["officeHours"]["begin"]
        self.office_hours_end = settings["officeHours"]["end"]
        self.debug = settings["debug"]

        self.channel_id = fetchChannelId(self.channel_name, self.userToken)
        self.post_URL = "https://" + self.team_domain + ".slack.com/services/hooks/slackbot?token=" + self.urlToken + "&channel=" + HASH + self.channel_name


################################################################################
    '''
    Selects an active user from a list of users
    '''
    def selectUser(self, exercise):
        active_users = self.fetchActiveUsers()

        # Add all active users not already in the user queue
        # Shuffles to randomly add new active users
        shuffle(active_users)
        bothArrays = set(active_users).intersection(self.user_queue)
        for user in active_users:
            if user not in bothArrays:
                self.user_queue.append(user)

        # The max number of users we are willing to look forward
        # to try and find a good match
        sliding_window = self.sliding_window_size

        # find a user to draw, priority going to first in
        for i in range(len(self.user_queue)):
            user = self.user_queue[i]

            # User should be active and not have done exercise yet
            if user in active_users and not user.hasDoneExercise(exercise):
                self.user_queue.remove(user)
                return user
            elif user in active_users:
                # Decrease sliding window by one. Basically, we don't want to jump
                # too far ahead in our queue
                sliding_window -= 1
                if sliding_window <= 0:
                    break

        # If everybody has done exercises or we didn't find a person within our sliding window,
        for user in self.user_queue:
            if user in active_users:
                self.user_queue.remove(user)
                return user

        # If we weren't able to select one, just pick a random
        print "Selecting user at random (queue length was " + str(len(self.user_queue)) + ")"
        return active_users[random.randrange(0, len(active_users))]


    '''
    Fetches a list of all active users in the channel
    '''
    def fetchActiveUsers(self):
        # Check for new members
        params = {"token": self.userToken, "channel": self.channel_id}
        response = requests.get("https://slack.com/api/channels.info", params=params)
        user_ids = json.loads(response.text, encoding='utf-8')["channel"]["members"]

        active_users = []

        for user_id in user_ids:
            # Add user to the cache if not already
            if user_id not in self.user_cache:
                self.user_cache[user_id] = User(user_id, self.userToken)
                if not self.first_run:
                    # Push our new users near the front of the queue!
                    self.user_queue.insert(2,self.user_cache[user_id])

            if self.user_cache[user_id].isActive():
                active_users.append(self.user_cache[user_id])

        if self.first_run:
            self.first_run = False

        return active_users

    '''
    Selects an exercise and start time, and sleeps until the time
    period has past.
    '''
    def selectExerciseAndStartTime(self):
        next_time_interval = self.selectNextTimeInterval()
        minute_interval = next_time_interval/60
        exercise = self.selectExercise()

        # Announcement String of next lottery time
        lottery_announcement = "NEXT LOTTERY FOR " + exercise["name"].upper() + " IS IN " + str(minute_interval) + (" MINUTES" if minute_interval != 1 else " MINUTE")

        # Announce the exercise to the thread
        if not self.debug:
            requests.post(self.post_URL, data=lottery_announcement)
        print lottery_announcement

        # Sleep the script until time is up
        if not self.debug:
            time.sleep(next_time_interval)
        else:
            # If debugging, once every 5 seconds
            time.sleep(5)

        return exercise


    '''
    Selects the next exercise
    '''
    def selectExercise(self):
        idx = random.randrange(0, len(self.exercises))
        return self.exercises[idx]


    '''
    Selects the next time interval
    '''
    def selectNextTimeInterval(self):
        return random.randrange(self.min_countdown * 60, self.max_countdown * 60)


    '''
    Selects a person to do the already-selected exercise
    '''
    def assignExercise(self, exercise):
        # Select number of reps
        exercise_reps = random.randrange(exercise["minReps"], exercise["maxReps"]+1)

        winner_announcement = str(exercise_reps) + " " + str(exercise["units"]) + " " + exercise["name"] + " RIGHT NOW "

        # EVERYBODY
        if random.random() < self.group_callout_chance:
            winner_announcement += "@channel!"

            # Populate the user_cache
            active_users = self.fetchActiveUsers()
            for user in active_users:
                user.addExercise(exercise, exercise_reps)
                self.logger.logExercise(user.getUserHandle(),exercise["name"],exercise_reps,exercise["units"], self.debug)

        else:
            winners = [self.selectUser(exercise) for i in range(self.num_people_per_callout)]

            for i in range(self.num_people_per_callout):
                winner_announcement += str(winners[i].getUserHandle())
                if i == self.num_people_per_callout - 2:
                    winner_announcement += ", and "
                elif i == self.num_people_per_callout - 1:
                    winner_announcement += "!"
                else:
                    winner_announcement += ", "

                winners[i].addExercise(exercise, exercise_reps)
                self.logger.logExercise(winners[i].getUserHandle(),exercise["name"],exercise_reps,exercise["units"], self.debug)

        # Announce the user
        if not self.debug:
            requests.post(self.post_URL, data=winner_announcement)
        print winner_announcement


    def printStats(self):
        # Write to the command console today's breakdown
        s = "```\n"
        #s += "Username\tAssigned\tComplete\tPercent
        s += "Username".ljust(15)
        for exercise in self.exercises:
            s += exercise["name"] + "  "
        s += "\n---------------------------------------------------------------\n"

        for user_id in self.user_cache:
            user = self.user_cache[user_id]
            s += user.username.ljust(15)
            for exercise in self.exercises:
                if exercise["id"] in user.exercises:
                    s += str(user.exercises[exercise["id"]]).ljust(len(exercise["name"]) + 2)
                else:
                    s += str(0).ljust(len(exercise["name"]) + 2)
            s += "\n"

            user.storeSession(str(datetime.datetime.now()))

        s += "```"

        if not self.debug:
            requests.post(self.post_URL, data=s)
        print s


    def saveUsers(self):
        # write to file
        if self.shouldCache:
            with open('user_cache.save','wb') as f:
                pickle.dump(self.user_cache,f)

    def isOfficeHours(self):
        if not self.office_hours_on:
            if self.debug:
                print "not office hours"
            return True
        now = datetime.datetime.now()
        now_time = now.time()
        if now_time >= datetime.time(self.office_hours_begin) and now_time <= datetime.time(self.office_hours_end):
            if self.debug:
                print "in office hours"
            return True
        else:
            if self.debug:
                print "out office hours"
            return False
