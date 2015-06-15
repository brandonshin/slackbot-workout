import random
import time
import requests
import json
import csv
import os
from User import User

# Environment variables must be set with your tokens
USER_TOKEN_STRING =  os.environ['SLACK_USER_TOKEN_STRING']
URL_TOKEN_STRING =  os.environ['SLACK_URL_TOKEN_STRING']

HASH = "%23"

DEBUG = True


# local cache of usernames
# maps userIds to usernames
user_cache = {}

# round robin store
priority_users = []

# Configuration values to be set in setConfiguration
class Bot:
    def __init__(self):
        self.setConfiguration()

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

        self.post_URL = "https://" + self.team_domain + ".slack.com/services/hooks/slackbot?token=%23" + URL_TOKEN_STRING + "&channel=" + HASH + self.channel_name


################################################################################
'''
Selects an active user from a list of users
'''
def selectUser(bot):
    active_users = fetchactive_users(bot)

    if len(priority_users) == 0:

    return active_users[random.randrange(0, len(active_users))]


'''
Fetches a list of all active users in the channel
'''
def fetchactive_users(bot):
    # Check for new members
    params = {"token": USER_TOKEN_STRING, "channel": bot.channel_id}
    response = requests.get("https://slack.com/api/channels.info", params=params)
    user_ids = json.loads(response.text, encoding='utf-8')["channel"]["members"]

    active_users = []

    for user_id in user_ids:
        # Add user to the cache if not already
        if user_id not in user_cache:
            user_cache[user_id] = User(user_id)

        if user_cache[user_id].isActive():
            active_users.append(user_cache[user_id])

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
        # If debugging, once every 10 seconds
        time.sleep(10)

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
    winner = selectUser(bot)

    winner_announcement = str(exercise_reps) + " " + str(exercise["units"]) + " " + exercise["name"] + " RIGHT NOW " + str(winner.getUserHandle())

    # Save the exercise to the user
    winner.addExercise(exercise, exercise_reps)

    # Announce the user
    if not DEBUG:
        requests.post(bot.post_URL, data=winner_announcement)
    print winner_announcement

    # log the exercise
    logExercise(winner.getUserHandle(),exercise["name"],exercise_reps,exercise["units"])


def logExercise(username,exercise,reps,units):
    with open("log.csv", 'a') as f:
        writer = csv.writer(f)
        writer.writerow([username,exercise,reps,units])

def saveUsers():
    for user_id in user_cache:
        print user_cache[user_id].exercise_history


def main():
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
        saveUsers()


main()
