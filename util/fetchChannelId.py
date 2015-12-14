'''
A method which gets the ID of a channel given its name.
'''

import requests
import json

HASH = "%23"

def fetchChannelId(channelName, userTokenString):
    params = {"token": userTokenString }

    # Capture Response as JSON
    response = requests.get("https://slack.com/api/channels.list", params=params)
    channels = json.loads(response.text, encoding='utf-8')["channels"]

    for channel in channels:
        if channel["name"] == channelName:
            return channel["id"]
            break
    return None
