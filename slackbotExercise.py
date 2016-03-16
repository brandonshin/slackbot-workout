import random
import time
import requests
import json
import csv
import sys
import os
from random import shuffle
import pickle
import os.path
import datetime
from datetime import timedelta
import psycopg2
import pprint
from User import User
from multiprocessing import Process
from Database import DB

# Environment variables must be set with your tokens
USER_TOKEN_STRING =  os.environ['SLACK_USER_TOKEN_STRING']
URL_TOKEN_STRING =  os.environ['SLACK_URL_TOKEN_STRING']
BAMBOO_API_KEY =  os.environ['BAMBOO_API_KEY']

EXERCISES_FOR_DAY = []

HASH = "%23"
    

# Configuration values to be set in setConfiguration
class Bot:
    def __init__(self, office_config_file):
        self.setConfiguration(office_config_file)

        if self.database:
            self.db = DB(self.channel_name.replace('-', ''))

        self.csv_filename = "log" + time.strftime("%Y%m%d-%H%M") + ".csv"
        self.first_run = True

        # local cache of usernames
        # maps userIds to usernames
        self.user_cache = self.loadUserCache()

        # round robin store
        self.user_queue = []

        self.last_listen_ts = '0'

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
    def setConfiguration(self, office_config_file):
        # Read variables fromt the configuration file
        with open(office_config_file) as f:
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
            self.user_id = settings["botUserId"]
            self.default_snooze_length = settings["defaultSnoozeLength"]

            self.debug = settings["debug"]
            self.database = settings["database"]

        self.post_message_URL = "https://slack.com/api/chat.postMessage?token=" + USER_TOKEN_STRING + "&channel=" + self.channel_id + "&as_user=true&link_names=1"

class Exercises:

    def __init__(self, exercise, exercise_reps, users, timestamp):

        self.exercise = exercise
        self.exercise_reps = exercise_reps
        self.users = users
        self.timestamp = timestamp
        self.count_of_acknowledged = 0
        self.time_assigned = time.time()

        self.completed_users = []
        self.refused_users = []
        self.snoozed_users = []

    def __str__(self):
        return "An instance of class Exercises with state: excercise=%s users=%s, timestamp=%s" % (self.exercise, self.users, self.timestamp)

    def __repr__(self):
        return 'Exercises("%s", "%s", "%s")' % (self.exercise, self.users, self.timestamp)

class Reminder:
    def __init__(self, exercise_timestamp_string, reminder_timestamp, userid, exercise):
        self.exercise_timestamp_string = exercise_timestamp_string
        self.reminder_timestamp = reminder_timestamp
        self.userid = userid
        self.has_been_processed = False
        self.exercise = exercise

################################################################################
'''
Selects an active user from a list of users
'''
def selectUser(bot, exercise, all_employees, previous_winners):
    active_users = fetchActiveUsers(bot, all_employees)

    if len(previous_winners) > 0:
        for previous_winner in previous_winners:
            active_users.remove(previous_winner)

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
Fetches all of the employees from Bamboohr
'''
def fetchAllEmployeesFromBamboo(bot):
    headers = {'Authorization': 'Basic %s' % BAMBOO_API_KEY, 'Accept':'application/json'}
    response = requests.get("https://api.bamboohr.com/api/gateway.php/hudl/v1/employees/directory", headers=headers)
    print "fetchAllEmployees response: " + response.text
    all_employees = []
    if response.ok:
        if bot.debug:
            print "called bamboo successfully"
        all_employees = json.loads(response.text)["employees"]

        if bot.debug:
            print "number of users " + str(len(all_employees))
    else:
        response.raise_for_status()
    return all_employees

'''
Fetches a list of all active users in the channel
'''
def fetchActiveUsers(bot, all_employees):
    # Check for new members
    params = {"token": USER_TOKEN_STRING, "channel": bot.channel_id}
    response = requests.get("https://slack.com/api/channels.info", params=params)
    print "fetchActiveUsers response: " + response.text
    user_ids = json.loads(response.text, encoding='utf-8')["channel"]["members"]

    active_users = []

    for user_id in user_ids:
        # Don't add hudl_workout
        if user_id != bot.user_id:
            # Add user to the cache if not already
            if user_id not in bot.user_cache:
                bot.user_cache[user_id] = User(user_id, all_employees)
                if not bot.first_run:
                    # Push our new users near the front of the queue!
                    bot.user_queue.insert(2,bot.user_cache[user_id])

            if bot.user_cache[user_id].isActive():
                active_users.append(bot.user_cache[user_id])

    if bot.first_run:
        bot.first_run = False

    return active_users

'''
Select time interval before next exercise
'''
def selectTimeInterval(bot):
    next_time_interval = selectNextTimeInterval(bot)
    return next_time_interval/60

def announceExercise(bot, minute_interval):

    exercise = selectExercise(bot)

    # Announcement String of next lottery time
    lottery_announcement = "NEXT LOTTERY FOR " + exercise["name"].upper() + " IS IN " + str(minute_interval) + (" MINUTES" if minute_interval != 1 else " MINUTE")

    # Announce the exercise to the thread
    if not bot.debug:
        response = requests.post(bot.post_message_URL + "&text=" + lottery_announcement)
        print "announceExercise response: " + response.text
        if bot.last_listen_ts == '0':
            bot.last_listen_ts = json.loads(response.text, encoding='utf-8')["ts"]
    print lottery_announcement
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
def assignExercise(bot, exercise, all_employees):
    # Select number of reps
    exercise_reps = random.randrange(exercise["minReps"], exercise["maxReps"]+1)

    winner_announcement = str(exercise_reps) + " " + str(exercise["units"]) + " " + exercise["name"] + " RIGHT NOW "

    winners = []
    # EVERYBODY
    if random.random() < bot.group_callout_chance:
        winner_announcement += "@channel!"

        for user_id in bot.user_cache:
            user = bot.user_cache[user_id]
            user.addExercise(exercise, exercise_reps)
            winners.append(user)
    else:
        for i in range(bot.num_people_per_callout):
            winners.append(selectUser(bot, exercise, all_employees, winners))

        for i in range(bot.num_people_per_callout):
            winner_announcement += str(winners[i].getUserHandle())
            if i == bot.num_people_per_callout - 2:
                winner_announcement += ", and "
            elif i == bot.num_people_per_callout - 1:
                winner_announcement += "!"
            else:
                winner_announcement += ", "

            winners[i].addExercise(exercise, exercise_reps)

    last_message_timestamp = str(datetime.datetime.now())
    # Announce the user
    if not bot.debug:
        response = requests.post(bot.post_message_URL + "&text=" + winner_announcement)
        print "assignExercise response: " + response.text
        last_message_timestamp = json.loads(response.text, encoding='utf-8')["ts"]
        requests.post("https://slack.com/api/reactions.add?token=" + USER_TOKEN_STRING + "&name=yes&channel=" + bot.channel_id + "&timestamp=" + last_message_timestamp +  "&as_user=true")
        requests.post("https://slack.com/api/reactions.add?token="+ USER_TOKEN_STRING + "&name=no&channel=" + bot.channel_id + "&timestamp=" + last_message_timestamp +  "&as_user=true")
        requests.post("https://slack.com/api/reactions.add?token="+ USER_TOKEN_STRING + "&name=sleeping&channel=" + bot.channel_id + "&timestamp=" + last_message_timestamp +  "&as_user=true")


    exercise_obj = Exercises(exercise, exercise_reps, winners, last_message_timestamp)
    EXERCISES_FOR_DAY.append(exercise_obj)
    logExercise(bot,winners,exercise["name"],exercise_reps,exercise["units"],exercise_obj.time_assigned)

    print winner_announcement


def logExercise(bot,winners,exercise,reps,units,timestamp):
    filename = bot.csv_filename + "_DEBUG" if bot.debug else bot.csv_filename
    for winner in winners:
        username = winner.getUserHandle()
        with open(filename, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([str(datetime.datetime.now()),username,exercise,reps,units,bot.debug])
        if bot.database:
            d = dict(username=username, exercise=exercise, reps=reps, assigned_at=timestamp)
            bot.db.assign(d)

def saveUsers(bot, dateOfExercise):
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
                exerciseUnitCount = countExercisesUnitsForDay(bot, exercise["id"], dateOfExercise, user);
                s += str(user.exercises[exercise["id"]]).ljust(len(exercise["name"]) + 2)
            else:
                s += str(0).ljust(len(exercise["name"]) + 2)
        s += "\n"

        user.storeSession(str(datetime.datetime.now()))

    s += "```"

    if not bot.debug:
        requests.post(bot.post_message_URL + "&text=" + s)
    print s


    # write to file
    with open('user_cache.save','wb') as f:
        pickle.dump(bot.user_cache,f)

def countExercisesUnitsForDay(bot, exerciseID, dayOfExerciseString, user):
    if bot.debug and dayOfExerciseString is not None:
        print "username " + user.username + " exercise ID " + str(exerciseID) + " Day " + str(dayOfExerciseString)
                                                            
    count = 0

    #count for all time if no day is sent
    if dayOfExerciseString is None:
        count = user.exercises[exerciseID]
    else:
        #loop through the history for matching days and exercise ID
        for exercise_history in user.exercise_history:
            if bot.debug:
                print str(exercise_history[0]) + "-" + str(exercise_history[1]) + "-" + exercise_history[2]+ "-" + str(exercise_history[3])
            if exercise_history[0][:10] == dayOfExerciseString[:10] and exercise_history[1] == exerciseID:
                count += exercise_history[3]
    return count

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

def initiateThrowdown(bot, all_employees, message):

    text = message['text'].lower()
    words = text.split()
    challengerId = message['user']

    active_users = fetchActiveUsers(bot, all_employees)
    challengees = []

    for user in active_users:
        if user.id == challengerId:
            challenger = user
            break

    exercise = findExerciseInText(bot, text)
    exercise_reps = findIntInText(bot, words)

    if challenger.has_challenged_today == True:
        already_challenged_text = 'You can only give out a challenge once a day ' + challenger.real_name
        requests.post(bot.post_message_URL + "&text=" + already_challenged_text)
        return

    if exercise_reps != False and exercise != False and exercise_reps > exercise['maxReps']:
        too_many_reps_text = 'Please select a number under ' + str(exercise['maxReps']) + ' for that exercise, ' + challenger.real_name
        requests.post(bot.post_message_URL + "&text=" + too_many_reps_text)
        return

    if challenger is not None and exercise != False and exercise_reps != False:
        for user in active_users:
            for word in words:
                if user.id.lower() in word:
                    challengees.append(user)
                    print "Found a challengee"

        if len(challengees) > 0:

            for challengee in challengees:
                challengee.addExercise(exercise, exercise_reps)

            challenger.has_challenged_today = True
            challenge_text = "You hear that, " + challengees[0].real_name + "? " + challenger.real_name + " is challenging you, " + str(exercise_reps) + " " + str(exercise["units"]) + " " + exercise['name'] + " now!"
            response = requests.post(bot.post_message_URL + "&text=" + challenge_text)
            print "initiateThrowdown response: " + response.text

            last_message_timestamp = json.loads(response.text, encoding='utf-8')["ts"]
            requests.post("https://slack.com/api/reactions.add?token=" + USER_TOKEN_STRING + "&name=yes&channel=" + bot.channel_id + "&timestamp=" + last_message_timestamp +  "&as_user=true")
            requests.post("https://slack.com/api/reactions.add?token="+ USER_TOKEN_STRING + "&name=no&channel=" + bot.channel_id + "&timestamp=" + last_message_timestamp +  "&as_user=true")
            requests.post("https://slack.com/api/reactions.add?token="+ USER_TOKEN_STRING + "&name=sleeping&channel=" + bot.channel_id + "&timestamp=" + last_message_timestamp +  "&as_user=true")

            exercise_obj = Exercises(exercise, exercise_reps, challengees, last_message_timestamp)
            EXERCISES_FOR_DAY.append(exercise_obj)
            logExercise(bot,challengees,exercise["name"],exercise_reps,exercise["units"],exercise_obj.time_assigned)

            print challenge_text

def findExerciseInText(bot, text):

    # Check for messages specific to a workout
    for exercise in bot.exercises:
        found_exercise = False
        listen_names = exercise['listenNames'].split(';')
        for listen_name in listen_names:
            if listen_name in text:
                return exercise

    return found_exercise

def findIntInText(bot, words):

    for word in words:
        if all(char.isdigit() for char in word):
            return int(word)

    return False

def resetChallenges(bot):

    for user_id in bot.user_cache:
        user = bot.user_cache[user_id]
        user.has_challenged_today = False

    print "Reset users' challenges"


def listenForReactions(bot):

    if not bot.debug:
        for exercise in EXERCISES_FOR_DAY:

            timestamp = exercise.timestamp
            response = requests.get("https://slack.com/api/reactions.get?token=" + USER_TOKEN_STRING + "&channel=" + bot.channel_id + "&full=1&timestamp=" + timestamp)
            if json.loads(response.text, encoding='utf-8')["ok"] == True:
                reactions = json.loads(response.text, encoding='utf-8')["message"]["reactions"]
                for reaction in reactions:
                    if reaction["name"] == "yes":
                        users_who_have_reacted_with_yes = reaction["users"]
                    elif reaction["name"] == "no":
                        users_who_have_reacted_with_no = reaction["users"]
                    elif reaction["name"] == "sleeping":
                        users_who_have_reacted_with_sleeping = reaction["users"]

                for user in exercise.users:
                    if user.id in users_who_have_reacted_with_yes and user not in exercise.completed_users:
                        exercise_name = exercise.exercise["name"]
                        print user.real_name + " has completed their " + exercise_name + " after " + str((time.time() - exercise.time_assigned)) + " seconds"
                        exercise.count_of_acknowledged += 1
                        exercise.completed_users.append(user)
                        if bot.database:
                            query = dict(username='@'+user.username, exercise=exercise_name, assigned_at=exercise.time_assigned, completed_at=time.time())
                            bot.db.complete(query)
                    elif user.id in users_who_have_reacted_with_no and user not in exercise.refused_users and user not in exercise.completed_users:
                        exercise_name = exercise.exercise["name"]
                        print user.real_name + " refuses to complete their " + exercise_name
                        exercise.refused_users.append(user)
                        exercise.count_of_acknowledged += 1
                    elif not isReminderInReminderList(user.id, exercise) and user.id in users_who_have_reacted_with_sleeping:
                        exercise.snoozed_users.append(Reminder(timestamp, datetime.datetime.now(), user.id, exercise))


                if exercise.count_of_acknowledged == len(exercise.users):
                    EXERCISES_FOR_DAY.remove(exercise)
                    print "Removing Exercise"

def isReminderInReminderList(userid, exercise):
    for reminder in exercise.snoozed_users:
        if userid == reminder.userid and exercise.timestamp == reminder.exercise_timestamp_string:
            return True
    return False

def remindPeopleForIncompleteExercisesAtEoD(bot):
    for exercise in EXERCISES_FOR_DAY:
        for user in exercise.users:
            if user not in exercise.completed_users and user not in exercise.refused_users:
                reminderMessage = user.getUserHandle() + " still needs to do " + str(exercise.exercise_reps) + " " + str(exercise.exercise["units"]) + " " + exercise.exercise["name"]
                if bot.debug:
                    print reminderMessage
                else:
                    requests.post(bot.post_message_URL + "&text=" + reminderMessage)


def remindTheSleepies(bot):
    for exercise in EXERCISES_FOR_DAY:
        for reminder in exercise.snoozed_users:
            if not reminder.has_been_processed:
                # if now is beyond the reminder timestamp plus the snooze length, then we should remind them
                # also, don't remind them if they completed/rejected the exercise after they were added to the reminders
                if datetime.datetime.now() >= reminder.reminder_timestamp + timedelta(minutes=bot.default_snooze_length) and reminder.userid not in exercise.completed_users and reminder.userid not in exercise.refused_users:
                    reminderMessage = bot.user_cache[reminder.userid].getUserHandle() + " still needs to do " + str(exercise.exercise_reps) + " " + str(exercise.exercise["units"]) + " " + exercise.exercise["name"]
                    if bot.debug:
                        print reminderMessage
                    else:
                        requests.post(bot.post_message_URL + "&text=" + reminderMessage)
                    reminder.has_been_processed = True

def listenForCommands(bot, all_employees):
    response = requests.get("https://slack.com/api/channels.history?token=" + USER_TOKEN_STRING + "&channel=" + bot.channel_id + "&oldest=" + bot.last_listen_ts)
    response_json = json.loads(response.text, encoding='utf-8')
    messages = response_json["messages"]
    if not messages:
        return

    last_time = messages[-1]['ts']
    bot.last_listen_ts = last_time
    command_start = '<@'+bot.user_id.lower()+'>'
    for message in messages:
        text = message['text'].lower()
        if text.startswith(command_start):

            if 'challenge' in text:
                initiateThrowdown(bot, all_employees, message)
                break

            exercise = findExerciseInText(bot, text)
            if exercise != False:
                requests.post(bot.post_message_URL + "&text=" + exercise['tutorial'])
                break

            # Check for help command
            if 'help' in text:
                help_message = 'Just send me a name of an exercise, and I will teach you how to do it.'
                for exercise in bot.exercises:
                    help_message += '\n ' + exercise['name']
                help_message += '\n If you want to issue a challenge say `@hudl_workout I challenge @PERSON to 15 EXERCISE`'
                requests.post(bot.post_message_URL + "&text=" + help_message)
                break

            else:
                prompt_actual_command = "I'm sorry, I can't understand you"
                requests.post(bot.post_message_URL + "&text=" + prompt_actual_command)


def main(argv):

    office_config_file = sys.argv[1]
    bot = Bot(office_config_file)
    isNewDay = False
    alreadyRemindedAtEoD = False

    time_to_announce = datetime.datetime.min
    exercise = None

    try:
        while True:
            if isOfficeHours(bot):

                # set new day based on the first time we entered office hours
                if not isNewDay:
                    EXERCISES_FOR_DAY = []
                    resetChallenges(bot)
                    isNewDay = True
                    alreadyRemindedAtEoD = False
                    # load all employees at the beginning of the day. Only once a day so we don't bombard bamboo
                    all_employees = fetchAllEmployeesFromBamboo(bot)
                    if bot.debug:
                        print "it's a new day"

                # Re-fetch config file if settings have changed
                bot.setConfiguration(office_config_file)

                if not bot.debug:
                    # Select time interval
                    if datetime.datetime.now() > time_to_announce:
                        # If there is an existing exercise, assign it
                        if exercise is not None:
                            assignExercise(bot, exercise, all_employees)

                        time_interval = selectTimeInterval(bot)
                        time_to_announce = datetime.datetime.now() + datetime.timedelta(0, time_interval * 60)

                        # Get an exercise to do
                        exercise = announceExercise(bot, time_interval)
                else:
                    if exercise is not None:
                        assignExercise(bot, exercise, all_employees)
                    time_interval = selectTimeInterval(bot)
                    time_to_announce = datetime.datetime.now() + datetime.timedelta(0, time_interval * 60)
                    exercise = announceExercise(bot, time_interval)


                listenForReactions(bot)
                listenForCommands(bot, all_employees)

                remindTheSleepies(bot)

                # remind slackers to do their workouts at the EoD
                endOfDay =  datetime.datetime.now().replace(hour=bot.office_hours_end, minute=0, second=0)
                if not alreadyRemindedAtEoD and (datetime.datetime.now() + timedelta(minutes=bot.max_countdown) > endOfDay):
                    if bot.debug:
                        print "People need a reminder"
                    remindPeopleForIncompleteExercisesAtEoD(bot)
                    alreadyRemindedAtEoD = True

                time.sleep(1)

            else:
                # write out the leaderboard the first time of the day we hit non-working hours
                if isNewDay:
                    if bot.debug:
                        print "it's the end of a day"
                    saveUsers(bot, str(datetime.datetime.now()))

                    # Reset all users to have challenges
                    resetChallenges(bot)
                    isNewDay = False

                # Sleep the script and check again for office hoursqa.hu
                if not bot.debug:
                    time.sleep(5*60) # Sleep 5 minutes
                else:
                    # If debugging, check again in 5 seconds
                    time.sleep(5)

    except KeyboardInterrupt:
        saveUsers(bot, str(datetime.datetime.now()))


main(sys.argv)
