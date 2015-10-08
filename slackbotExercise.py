import random
import time
import requests
import json
import csv
import os
from random import shuffle
import pickle
import os.path
import datetime

from User import User

# Environment variables must be set with your tokens
USER_TOKEN_STRING =  os.environ['SLACK_USER_TOKEN_STRING']
URL_TOKEN_STRING =  os.environ['SLACK_URL_TOKEN_STRING']

HASH = "%23"


# Configuration values to be set in setConfiguration
class Bot:
    def __init__(self):
        self.setConfiguration()

        self.csv_filename = "log" + time.strftime("%Y%m%d-%H%M") + ".csv"
        self.first_run = True

        # local cache of usernames
        # maps userIds to usernames
        self.user_cache = self.loadUserCache()

        # round robin store
        self.user_queue = []


    def loadUserCache(self):
        if os.path.isfile('user_cache.save'):
            with open('user_cache.save','rb') as f:
                self.user_cache = pickle.load(f)
                print "Loading " + str(len(self.user_cache)) + " users from cache."
                return self.user_cache

        return {}

    '''
    Sets the configuration file.

    Runs after every callout so that settings can be changed realtime
    '''
    def setConfiguration(self):
        # Read variables fromt the configuration file
        with open('config.json') as f:
            settings = json.load(f)

            self.team_domain = settings["teamDomain"]
            self.channel_name = settings["channelName"]
            self.min_countdown = settings["callouts"]["timeBetween"]["minTime"]
            self.max_countdown = settings["callouts"]["timeBetween"]["maxTime"]
            self.num_people_per_callout = settings["callouts"]["numPeople"]
            self.sliding_window_size = settings["callouts"]["slidingWindowSize"]
            self.group_callout_chance = settings["callouts"]["groupCalloutChance"]
            self.channel_id = settings["channelId"]
            self.exercises = settings["exercises"]
            self.office_hours_on = settings["officeHours"]["on"]
            self.office_hours_begin = settings["officeHours"]["begin"]
            self.office_hours_end = settings["officeHours"]["end"]

            self.debug = settings["debug"]

        self.post_URL = "https://" + self.team_domain + ".slack.com/services/hooks/slackbot?token=" + URL_TOKEN_STRING + "&channel=" + HASH + self.channel_name


################################################################################
'''
Selects an active user from a list of users
'''
def selectUser(bot, exercise):
    active_users = fetchActiveUsers(bot)

    # Add all active users not already in the user queue
    # Shuffles to randomly add new active users
    shuffle(active_users)
    bothArrays = set(active_users).intersection(bot.user_queue)
    for user in active_users:
        if user not in bothArrays:
            bot.user_queue.append(user)

    # The max number of users we are willing to look forward
    # to try and find a good match
    sliding_window = bot.sliding_window_size

    # find a user to draw, priority going to first in
    for i in range(len(bot.user_queue)):
        user = bot.user_queue[i]

        # User should be active and not have done exercise yet
        if user in active_users and not user.hasDoneExercise(exercise):
            bot.user_queue.remove(user)
            return user
        elif user in active_users:
            # Decrease sliding window by one. Basically, we don't want to jump
            # too far ahead in our queue
            sliding_window -= 1
            if sliding_window <= 0:
                break

    # If everybody has done exercises or we didn't find a person within our sliding window,
    for user in bot.user_queue:
        if user in active_users:
            bot.user_queue.remove(user)
            return user

    # If we weren't able to select one, just pick a random
    print "Selecting user at random (queue length was " + str(len(bot.user_queue)) + ")"
    return active_users[random.randrange(0, len(active_users))]


'''
Fetches a list of all active users in the channel
'''
def fetchActiveUsers(bot):
    # Check for new members
    params = {"token": USER_TOKEN_STRING, "channel": bot.channel_id}
    response = requests.get("https://slack.com/api/channels.info", params=params)
    user_ids = json.loads(response.text, encoding='utf-8')["channel"]["members"]

    active_users = []

    for user_id in user_ids:
        # Add user to the cache if not already
        if user_id not in bot.user_cache:
            bot.user_cache[user_id] = User(user_id)
            if not bot.first_run:
                # Push our new users near the front of the queue!
                bot.user_queue.insert(2,bot.user_cache[user_id])

        if bot.user_cache[user_id].isActive():
            active_users.append(bot.user_cache[user_id])

    if bot.first_run:
        bot.first_run = False

    return active_users

'''
Selects an exercise and start time, and sleeps until the time
period has past.
'''
def selectExerciseAndStartTime(bot):
    next_time_interval = selectNextTimeInterval(bot)
    minute_interval = next_time_interval/60
    exercise = selectExercise(bot)

    # Announcement String of next lottery time
    lottery_announcement = "NEXT LOTTERY FOR " + exercise["name"].upper() + " IS IN " + str(minute_interval) + (" MINUTES" if minute_interval != 1 else " MINUTE")

    # Announce the exercise to the thread
    if not bot.debug:
        requests.post(bot.post_URL, data=lottery_announcement)
    print lottery_announcement

    # Sleep the script until time is up
    if not bot.debug:
        time.sleep(next_time_interval)
    else:
        # If debugging, once every 5 seconds
        time.sleep(5)

    return exercise


'''
Selects the next exercise
'''
def selectExercise(bot):
    idx = random.randrange(0, len(bot.exercises))
    return bot.exercises[idx]


'''
Selects the next time interval
'''
def selectNextTimeInterval(bot):
    return random.randrange(bot.min_countdown * 60, bot.max_countdown * 60)


'''
Selects a person to do the already-selected exercise
'''
def assignExercise(bot, exercise):
    # Select number of reps
    exercise_reps = random.randrange(exercise["minReps"], exercise["maxReps"]+1)

    winner_announcement = str(exercise_reps) + " " + str(exercise["units"]) + " " + exercise["name"] + " RIGHT NOW "

    # EVERYBODY
    if random.random() < bot.group_callout_chance:
        winner_announcement += "@channel!"

        for user_id in bot.user_cache:
            user = bot.user_cache[user_id]
            user.addExercise(exercise, exercise_reps)

        logExercise(bot,"@channel",exercise["name"],exercise_reps,exercise["units"])

    else:
        winners = [selectUser(bot, exercise) for i in range(bot.num_people_per_callout)]

        for i in range(bot.num_people_per_callout):
            winner_announcement += str(winners[i].getUserHandle())
            if i == bot.num_people_per_callout - 2:
                winner_announcement += ", and "
            elif i == bot.num_people_per_callout - 1:
                winner_announcement += "!"
            else:
                winner_announcement += ", "

            winners[i].addExercise(exercise, exercise_reps)
            logExercise(bot,winners[i].getUserHandle(),exercise["name"],exercise_reps,exercise["units"])

    # Announce the user
    if not bot.debug:
        requests.post(bot.post_URL, data=winner_announcement)
    print winner_announcement


def logExercise(bot,username,exercise,reps,units):
    filename = bot.csv_filename + "_DEBUG" if bot.debug else bot.csv_filename
    with open(filename, 'a') as f:
        writer = csv.writer(f)

        writer.writerow([str(datetime.datetime.now()),username,exercise,reps,units,bot.debug])

def saveUsers(bot):
    # Write to the command console today's breakdown
    s = "```\n"
    #s += "Username\tAssigned\tComplete\tPercent
    s += "Username".ljust(15)
    for exercise in bot.exercises:
        s += exercise["name"] + "  "
    s += "\n---------------------------------------------------------------\n"

    for user_id in bot.user_cache:
        user = bot.user_cache[user_id]
        s += user.username.ljust(15)
        for exercise in bot.exercises:
            if exercise["id"] in user.exercises:
                s += str(user.exercises[exercise["id"]]).ljust(len(exercise["name"]) + 2)
            else:
                s += str(0).ljust(len(exercise["name"]) + 2)
        s += "\n"

        user.storeSession(str(datetime.datetime.now()))

    s += "```"

    if not bot.debug:
        requests.post(bot.post_URL, data=s)
    print s


    # write to file
    with open('user_cache.save','wb') as f:
        pickle.dump(bot.user_cache,f)

def isOfficeHours(bot):
    if not bot.office_hours_on:
        if bot.debug:
            print "not office hours"
        return True
    now = datetime.datetime.now()
    now_time = now.time()
    if now_time >= datetime.time(bot.office_hours_begin) and now_time <= datetime.time(bot.office_hours_end):
        if bot.debug:
            print "in office hours"
        return True
    else:
        if bot.debug:
            print "out office hours"
        return False

def main():
    bot = Bot()

    try:
        while True:
            if isOfficeHours(bot):
                # Re-fetch config file if settings have changed
                bot.setConfiguration()

                # Get an exercise to do
                exercise = selectExerciseAndStartTime(bot)

                # Assign the exercise to someone
                assignExercise(bot, exercise)

            else:
                # Sleep the script and check again for office hours
                if not bot.debug:
                    time.sleep(5*60) # Sleep 5 minutes
                else:
                    # If debugging, check again in 5 seconds
                    time.sleep(5)

    except KeyboardInterrupt:
        saveUsers(bot)


main()
