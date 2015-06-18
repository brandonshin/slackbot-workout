import random
import time
import requests
import json
import csv
import os
from random import shuffle
import pickle
import os.path
import time
from datetime import datetime

from User import User

# Environment variables must be set with your tokens
USER_TOKEN_STRING =  os.environ['SLACK_USER_TOKEN_STRING']
URL_TOKEN_STRING =  os.environ['SLACK_URL_TOKEN_STRING']

HASH = "%23"

DEBUG = True
FIRST_RUN = True


# local cache of usernames
# maps userIds to usernames
user_cache = {}

# round robin store
user_queue = []

# Configuration values to be set in setConfiguration
class Bot:
    def __init__(self):
        self.setConfiguration()

        self.csv_filename = "log" + time.strftime("%Y%m%d-%H%M") + ".csv"

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
            self.min_countdown = settings["timeBetweenCallouts"]["minTime"]
            self.max_countdown = settings["timeBetweenCallouts"]["maxTime"]
            self.channel_id = settings["channelId"]
            self.exercises = settings["exercises"]

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
    bothArrays = set(active_users).intersection(user_queue)
    for user in active_users:
        if user not in bothArrays:
            user_queue.append(user)

    # The max number of users we are willing to look forward
    # to try and find a good match
    sliding_window = 4

    # find a user to draw, priority going to first in
    for i in range(len(user_queue)):
        user = user_queue[i]

        # User should be active and not have done exercise yet
        if user in active_users and not user.hasDoneExercise(exercise):
            user_queue.remove(user)
            return user
        elif user in active_users:
            # Decrease sliding window by one. Basically, we don't want to jump
            # too far ahead in our queue
            sliding_window -= 1
            if sliding_window <= 0:
                break

    # If everybody has done exercises or we didn't find a person within our sliding window,
    for user in user_queue:
        if user in active_users:
            user_queue.remove(user)
            return user

    # If we weren't able to select one, just pick a random
    print "Selecting user at random (queue length was " + str(len(user_queue)) + ")"
    return active_users[random.randrange(0, len(active_users))]


'''
Fetches a list of all active users in the channel
'''
def fetchActiveUsers(bot):
    global DEBUG
    global FIRST_RUN

    # Check for new members
    params = {"token": USER_TOKEN_STRING, "channel": bot.channel_id}
    response = requests.get("https://slack.com/api/channels.info", params=params)
    user_ids = json.loads(response.text, encoding='utf-8')["channel"]["members"]

    active_users = []

    for user_id in user_ids:
        # Add user to the cache if not already
        if user_id not in user_cache:
            user_cache[user_id] = User(user_id)
            if not FIRST_RUN:
                # Push our new users near the front of the queue! 
                user_queue.insert(2,user_cache[user_id])

        if user_cache[user_id].isActive():
            active_users.append(user_cache[user_id])

    if FIRST_RUN:
        FIRST_RUN = False

    return active_users

'''
Selects an exercise and start time, and sleeps until the time
period has past.
'''
def selectExerciseAndStartTime(bot):
    next_time_interval = selectNextTimeInterval(bot)
    exercise = selectExercise(bot)

    # Announcement String of next lottery time
    lottery_announcement = "NEXT LOTTERY FOR " + exercise["name"].upper() + " IS IN " + str(next_time_interval/60) + " MINUTES"

    # Announce the exercise to the thread
    if not DEBUG:
        requests.post(bot.post_URL, data=lottery_announcement)
    print lottery_announcement

    # Sleep the script until time is up
    if not DEBUG:
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
    winner1 = selectUser(bot, exercise)
    winner2 = selectUser(bot, exercise)

    winner_announcement = str(exercise_reps) + " " + str(exercise["units"]) + " " + exercise["name"] + " RIGHT NOW " + str(winner1.getUserHandle()) + " and " + str(winner2.getUserHandle()) + "!"

    # Save the exercise to the user
    winner1.addExercise(exercise, exercise_reps)
    winner2.addExercise(exercise, exercise_reps)

    # Announce the user
    if not DEBUG:
        requests.post(bot.post_URL, data=winner_announcement)
    print winner_announcement

    # log the exercise
    logExercise(bot,winner1.getUserHandle(),exercise["name"],exercise_reps,exercise["units"])
    logExercise(bot,winner2.getUserHandle(),exercise["name"],exercise_reps,exercise["units"])


def logExercise(bot,username,exercise,reps,units):
    with open(bot.csv_filename, 'a') as f:
        writer = csv.writer(f)

        writer.writerow([str(datetime.now()),username,exercise,reps,units])

def saveUsers(bot):
    # Write to the command console today's breakdown
    s = "```\n"
    #s += "Username\tAssigned\tComplete\tPercent
    s += "Username".ljust(15)
    for exercise in bot.exercises:
        s += exercise["name"] + "  "
    s += "\n--------------------------------------------------------\n"

    for user_id in user_cache:
        user = user_cache[user_id]
        s += user.username.ljust(15)
        for exercise in bot.exercises:
            if exercise["id"] in user.exercises:
                s += str(user.exercises[exercise["id"]]).ljust(len(exercise["name"]) + 2)
            else:
                s += str(0).ljust(len(exercise["name"]) + 2)
        s += "\n"

    s += "```"

    if not DEBUG:
        requests.post(bot.post_URL, data=s)
    print s


    # write to file
    with open('user_cache.save','wb') as f:
        # print "============"
        # print pickle.dumps(user_cache)
        # print "================================================="
        # for user_id in user_cache:
        #     print pickle.dumps(user_cache[user_id])
        pickle.dump(user_cache,f)


def main():
    if os.path.isfile('user_cache.save'):
        with open('user_cache.save','rb') as f:
            user_cache = pickle.load(f)
            print len(user_cache)
            print user_cache

    bot = Bot()

    try:
        while True:
            # Re-fetch config file if settings have changed
            bot.setConfiguration()

            # Get an exercise to do
            exercise = selectExerciseAndStartTime(bot)

            # Assign the exercise to someone
            assignExercise(bot, exercise)
    except KeyboardInterrupt:
        saveUsers(bot)


main()
