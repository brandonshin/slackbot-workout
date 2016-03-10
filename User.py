import os
import requests
import json
import datetime
from pprint import pprint

# Environment variables must be set with your tokens
USER_TOKEN_STRING =  os.environ['SLACK_USER_TOKEN_STRING']

class User:

    def __init__(self, user_id, all_employees):
        # The Slack ID of the user
        self.id = user_id

        # The username (@username) and real name
        self.username, self.real_name = self.fetchNames()

        #The location from Bamboo's HR information
        self.location = self.fetchLocation(all_employees)
        
        # A list of all exercises done by user
        self.exercise_history = []

        # A record of all exercise totals (quantity)
        self.exercises = {}

        # A record of exercise counts (# of times)
        self.exercise_counts = {}

        # A record of past runs
        self.past_workouts = {}

        print "New user: " + self.real_name + " (" + self.username + ")"


    def storeSession(self, run_name):
        try:
            self.past_workouts[run_name] = self.exercises
        except:
            self.past_workouts = {}

        self.past_workouts[run_name] = self.exercises
        self.exercises = {}
        self.exercise_counts = {}


    def fetchNames(self):
        params = {"token": USER_TOKEN_STRING, "user": self.id}
        response = requests.get("https://slack.com/api/users.info",
                params=params)
        user_obj = json.loads(response.text, encoding='utf-8')["user"]

        username = user_obj["name"]
        real_name = user_obj["profile"]["real_name"]

        return username, real_name

    def getUserHandle(self):
        return ("@" + self.username).encode('utf-8')

    #parse through all of the employee list to find a matching name
    def fetchLocation(self, all_employees):
        location = ""
        for employee in all_employees:
            if employee["displayName"] == self.real_name or ((employee["nickname"] is not None and employee["nickname"] + " " + employee["lastName"]) == self.real_name):
                location = employee["location"]
                break
        return location
    '''
    Returns true if a user is currently "active", else false
    '''
    def isAvailable(self):
        try:
            #check if the user is active
            params = {"token": USER_TOKEN_STRING, "user": self.id}
            response = requests.get("https://slack.com/api/users.getPresence",
                    params=params)
            status = json.loads(response.text, encoding='utf-8')["presence"]
            isAvailable = False
            if status == "active":
                isAvailable = True

            # also check if user is in DND mode
            params = {"token": USER_TOKEN_STRING, "user": self.id}
            response = requests.get("https://slack.com/api/dnd.info",params=params)
            dnd_obj = json.loads(response.text, encoding='utf-8')


            isNowDuringDNDTime = (datetime.datetime.fromtimestamp(dnd_obj["next_dnd_start_ts"]) < datetime.datetime.now() and
                datetime.datetime.fromtimestamp(dnd_obj["next_dnd_end_ts"]) > datetime.datetime.now())

            # if DND is disabled OR
            # if now is before the start date and after the end date, then the user is not in DND mode
            if not dnd_obj["dnd_enabled"] or not isNowDuringDNDTime:
                isAvailable &= True
            elif isNowDuringDNDTime:
                isAvailable = False

            isSnoozeEnabled = False

            # slack doesn't return this variable unless it's ever been set by the user. So, we just ignore it if it's not there
            try:
                isSnoozeEnabled = dnd_obj["snooze_enabled"]
                print self.username + " - " + str(isSnoozeEnabled)
            except KeyError as e:
                # do nothing
                pass

            isAvailable &= (not isSnoozeEnabled)
            return isAvailable
        except requests.exceptions.ConnectionError:
            print "Error fetching online status for " + self.getUserHandle()
            return False

    def addExercise(self, exercise, reps):
        # Add to total counts
        self.exercises[exercise["id"]] = self.exercises.get(exercise["id"], 0) + reps
        self.exercise_counts[exercise["id"]] = self.exercise_counts.get(exercise["id"], 0) + 1

        # Add to exercise history record
        self.exercise_history.append([str(datetime.datetime.now()),exercise["id"],exercise["name"],reps,exercise["units"]])

    def hasDoneExercise(self, exercise):
        return exercise["id"] in self.exercise_counts

