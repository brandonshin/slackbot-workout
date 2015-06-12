import random
import time
import requests
import json
import csv
import os

USERTOKENSTRING = os.environ['USERTOKENSTRING']
URLTOKENSTRING = os.environ['URLTOKENSTRING']
CHANNEL = os.environ['CHANNEL']
CHANNELNAME = os.environ['CHANNELNAME']

def extractSlackUsers(token):
    # Set token parameter of Slack API call
    tokenString = token
    params = {"token": tokenString}

    # Capture Response as JSON
    response = requests.get("https://slack.com/api/users.list", params=params)
    users = json.loads(response.text, encoding='utf-8')["members"]

    # Get those in ROOM
    params["channel"] = CHANNEL
    response2 = requests.get("https://slack.com/api/channels.info", params=params)
    channel = json.loads(response2.text, encoding='utf-8')["channel"]
    channel_members = channel["members"]

    def findUserNames(x):
        if getStats(x) == False:
            return None
        name = "@" + x["name"].encode('utf-8')
        return name.encode('utf-8')
    def getStats(x):
        if x["id"] in channel_members:
	        params = {"token": tokenString, "user": x["id"]}
		response = requests.get("https://slack.com/api/users.getPresence", params=params)
		status = json.loads(response.text, encoding='utf-8')["presence"]
		return status == "active"
	else:
		return False

    return filter(None, list(map(findUserNames, users)))

def selectExerciseAndStartTime():

    # Exercise (2 Forms of Strings)
    exercises = [" PUSHUPS ", " PUSHUPS ", " SECOND PLANK ", " SITUPS ", " SECOND WALL SIT "]
    exerciseAnnouncements = ["PUSHUPS", "PUSHUPS", "PLANK", "SITUPS", "WALLSIT"]

    # Random Number generator for Reps/Seconds and Exercise
    nextTimeInterval = random.randrange(150, 900)
    exerciseIndex = random.randrange(0, 5)

    # Announcement String of next lottery time
    lotteryTimeString = "NEXT LOTTERY FOR " + str(exerciseAnnouncements[exerciseIndex]) + " IS IN " + str(nextTimeInterval/60) + " MINUTES"
    print lotteryTimeString
    
    requests.post("https://uacf.slack.com/services/hooks/slackbot?token="+URLTOKENSTRING+"&channel=%23" + CHANNELNAME, data=lotteryTimeString)

    time.sleep(nextTimeInterval)

    return str(exercises[exerciseIndex])


def selectPerson(exercise):

    # Select number of reps
    exerciseReps = random.randrange(25, 50)

    # Pull all users from API
    slackUsers = extractSlackUsers(USERTOKENSTRING)

    # Select index of team member from array of team members
    selection = random.randrange(0, len(slackUsers))

    lotteryWinnerString = str(exerciseReps) + str(exercise) + "RIGHT NOW " + slackUsers[selection]
    print lotteryWinnerString
    requests.post("https://uacf.slack.com/services/hooks/slackbot?token="+URLTOKENSTRING+"&channel=%23" + CHANNELNAME, data=lotteryWinnerString)

    with open("results.csv", 'a') as f:
        writer = csv.writer(f)
        writer.writerow([slackUsers[selection], exerciseReps, exercise])

for i in range(10000):
    exercise = selectExerciseAndStartTime()
    selectPerson(exercise)


