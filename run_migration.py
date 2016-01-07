from slackbot_workout.configurators import YamlFileConfigurationProvider
from slackbot_workout.migrations import UsernameToUserIdMigration
from slackbot_workout.api import SlackbotApi

config = YamlFileConfigurationProvider('config.yaml')
api = SlackbotApi(config, token='xoxp-2499669547-10707224704-15892141524-4b7e5a03b7')
migration = UsernameToUserIdMigration('flexecution', 'flexecution_copy', api)
