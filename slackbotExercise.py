import random
import time
import requests
import json
import csv

# Set your config variables from the config.json file
with open('config.json') as f:
    settings = json.load(f)
    USERTOKENSTRING = settings['USERTOKENSTRING']
    URLTOKENSTRING = settings["URLTOKENSTRING"]
    TEAMNAMESTRING = settings["TEAMNAMESTRING"]


# Extracts online users from Slack API
def extractSlackUsers(token):
    # Set token parameter of Slack API call
    tokenString = token
    params = {"token": tokenString}

    # Capture Response as JSON
    response = requests.get("https://slack.com/api/users.list", params=params)
    users = json.loads(response.text, encoding='utf-8')["members"]

    def findUserNames(x):
        if getStats(x) is False:
            return None
        name = "@" + x["name"].encode('utf-8')
        return name.encode('utf-8')

    def getStats(x):
        params = {"token": tokenString, "user": x["id"]}
        response = requests.get("https://slack.com/api/users.getPresence", params=params)
        status = json.loads(response.text, encoding='utf-8')["presence"]
        return status == "active"

    return filter(None, list(map(findUserNames, users)))


# Selects Next Time Interval and Returns the Exercise
def selectExerciseAndStartTime():

    # Exercise (2 Forms of Strings)
    exercises = [" PUSHUPS ", " PUSHUPS ", " SECOND PLANK ", " SITUPS ", " SECOND WALL SIT "]
    exerciseAnnouncements = ["PUSHUPS", "PUSHUPS", "PLANK", "SITUPS", "WALLSIT"]

    # Random Number generator for Reps/Seconds and Exercise
    nextTimeInterval = random.randrange(300, 1800)
    exerciseIndex = random.randrange(0, 5)

    # Announcement String of next lottery time
    lotteryTimeString = "NEXT LOTTERY FOR " + str(exerciseAnnouncements[exerciseIndex]) + " IS IN " + str(nextTimeInterval/60) + " MINUTES"

    # POST next lottery announcement to Slack
    requests.post("https://" + TEAMNAMESTRING + ".slack.com/services/hooks/slackbot?token="+URLTOKENSTRING+"&channel=%23general", data=lotteryTimeString)

    # Sleep until next lottery announcement
    time.sleep(nextTimeInterval)

    # Return exercise
    return str(exercises[exerciseIndex])


# Selects the exercise lottery winner
def selectPerson(exercise):

    # Select number of reps
    exerciseReps = random.randrange(25, 50)

    # Pull all users from API
    slackUsers = extractSlackUsers(USERTOKENSTRING)

    # Select index of team member from array of team members
    selection = random.randrange(0, len(slackUsers))

    # Select lottery winner
    lotteryWinnerString = str(exerciseReps) + str(exercise) + "RIGHT NOW " + slackUsers[selection]
    print lotteryWinnerString

    # POST to Slack
    requests.post("https://" + TEAMNAMESTRING + ".slack.com/services/hooks/slackbot?token="+URLTOKENSTRING+"&channel=%23general", data=lotteryWinnerString)

    # Record exercise entry in csv
    with open("results.csv", 'a') as f:
        writer = csv.writer(f)
        writer.writerow([slackUsers[selection], exerciseReps, exercise])

for i in range(10000):
    exercise = selectExerciseAndStartTime()
    selectPerson(exercise)


