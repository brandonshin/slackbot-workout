'''
A quick script to fetch the id of a channel you want to use.

USAGE: python fetchChannelId.py <channel_name>
'''

import requests
import sys
import os
import json

# Environment variables must be set with your tokens
USER_TOKEN_STRING =  os.environ['SLACK_USER_TOKEN_STRING']
URL_TOKEN_STRING =  os.environ['SLACK_URL_TOKEN_STRING']

HASH = "%23"

channelName = sys.argv[1]

params = {"token": USER_TOKEN_STRING }

# Capture Response as JSON
response = requests.get("https://slack.com/api/channels.list", params=params)
channels = json.loads(response.text, encoding='utf-8')["channels"]

for channel in channels:
    if channel["name"] == channelName:
        print(channel["id"])
        break
