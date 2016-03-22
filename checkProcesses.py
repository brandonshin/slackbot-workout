import os
import re
import requests
import subprocess

def postMessage(message):
    postMessageURL = "https://slack.com/api/chat.postMessage?token=" + os.environ['SLACK_USER_TOKEN_STRING'] + "&channel=" + os.environ['SLACK_ADMIN_CHANNEL_ID'] + "&as_user=true&link_names=1&text=" + message
    requests.post(postMessageURL)

def findProcess( city ):
    ps= subprocess.Popen("ps -ef | grep " + city + " | grep -v grep", shell=True, stdout=subprocess.PIPE)
    output = ps.stdout.read()
    ps.stdout.close()
    ps.wait()
    return output

def isProcessRunning( city ):
    output = findProcess( city )
    if re.search(city, output) is None:
        return False
    else:
        return True

cities = ['boston', 'omaha', 'london']

for city in cities:
    if not isProcessRunning(city):
        postMessage("@channel: " + city + " is not running right now")
    else:
        print city + " is running"

