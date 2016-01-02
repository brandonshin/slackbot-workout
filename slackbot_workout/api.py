import logging

from slacker import Slacker

class SlackbotApi(Slacker):
    def __init__(self, configuration, **kwargs):
        super(SlackbotApi, self).__init__(**kwargs)
        self.logger = logging.getLogger(__name__)
        self.configuration = configuration
        self.load_configuration()

    def load_configuration(self):
        config_dict = self.configuration.get_configuration()
        self.channel_id = self.fetch_channel_id(config_dict['channelName'])
        self.bot_name = config_dict['botName']

    def fetch_channel_id(self, channel_name):
        channels = self.channels.list()
        for channel in channels.body['channels']:
            if channel['name'] == channel_name:
                return channel['id']
        return None

    def post_flex_message(self, message):
        self.logger.debug("Sending message: %s", message)
        self.chat.post_message(self.channel_id, message, username=self.bot_name,
                icon_emoji=':muscle:')

    def get_members(self):
        response = self.channels.info(self.channel_id).body
        return response['channel']['members']

    def get_user_info(self, user_id):
        return self.users.info(user_id).body['user']

    def is_active(self, user_id):
        response =  self.users.get_presence(user_id).body
        return response["presence"] == "active"
