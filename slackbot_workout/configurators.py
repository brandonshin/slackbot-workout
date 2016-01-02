from abc import ABCMeta, abstractmethod
import json
import os
import yaml

class TokenProvider(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_user_token(self):
        pass

class EnvironmentTokenProvider(TokenProvider):
    def get_user_token(self):
        return os.environ['SLACK_USER_TOKEN_STRING']

class InMemoryTokenProvider(TokenProvider):
    def __init__(self, user_token):
        self.user_token = user_token

    def get_user_token(self):
        return self.user_token

class ConfigurationProvider(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_configuration(self):
        pass

class JsonFileConfigurationProvider(ConfigurationProvider):
    def __init__(self, filename):
        self.filename = filename

    def get_configuration(self):
        with open(self.filename, 'r') as f:
            return json.load(f)

class YamlFileConfigurationProvider(ConfigurationProvider):
    def __init__(self, filename):
        self.filename = filename

    def get_configuration(self):
        with open(self.filename, 'r') as f:
            return yaml.load(f)

class InMemoryConfigurationProvider(ConfigurationProvider):
    def __init__(self, configuration):
        self.set_configuration(configuration)

    def set_configuration(self, configuration):
        self.configuration = configuration

    def update_configuration(self, updates):
        self.configuration.update(updates)

    def get_configuration(self):
        return self.configuration

