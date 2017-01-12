import json

def parseSlackJSON(response):
    isMessageOkay = False
    try:
        if response.ok:
            parsed_message = json.loads(response.text, encoding='utf-8')
        else:
            print "Response is not okay: " + str(response.status_code) + ", text: " + response.text

        isMessageOkay = response.ok and parsed_message["ok"]
    except:
        print "Caught exception parsing response status: " + str(response.status_code) + ", text: " + response.text
        parsed_message = None
        isMessageOkay = False

    return parsed_message, isMessageOkay