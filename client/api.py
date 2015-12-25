from slacker import Slacker

class SlackbotApi(Slacker):
    def fetch_channel_id(self, channel_name):
        channels = self.channels.list()
        for channel in channels.body['channels']:
            if channel['name'] == channel_name:
                return channel['id']
        return None
