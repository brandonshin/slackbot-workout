import logging

from slacker import Slacker

class FlexbotApiClient(Slacker):
    def __init__(self, configuration, **kwargs):
        super(FlexbotApiClient, self).__init__(**kwargs)
        self.logger = logging.getLogger(__name__)
        self.configuration = configuration
        self.current_channel_name = None
        self.current_channel_id = self.channel_id()

    def channel_id(self):
        if self.configuration.channel_name() == self.current_channel_name:
            return self.current_channel_id
        else:
            self.current_channel_name = self.configuration.channel_name()
            channels = self.channels.list()
            for channel in channels.body['channels']:
                if channel['name'] == self.configuration.channel_name():
                    return channel['id']
            return None

    def bot_name(self):
        return self.configuration.bot_name()

    def post_flex_message(self, message):
        self.logger.debug("Sending message: %s", message)
        self.chat.post_message(self.channel_id(), message, username=self.bot_name(),
                icon_emoji=':muscle:')

    def get_members(self):
        response = self.channels.info(self.channel_id()).body
        return response['channel']['members']

    def get_user_info(self, user_id):
        return self.users.info(user_id).body['user']

    def is_active(self, user_id):
        response =  self.users.get_presence(user_id).body
        return response["presence"] == "active"
