import json
import os
from abc import ABCMeta, abstractmethod

class TokenProvider:
    __metaclass__ = ABCMeta

    @abstractmethod
    def getUserToken(self):
        pass

    @abstractmethod
    def getUrlToken(self):
        pass

class EnvironmentTokenProvider(TokenProvider):
    def getUserToken(self):
        return os.environ['SLACK_USER_TOKEN_STRING']

    def getUrlToken(self):
        return os.environ['SLACK_URL_TOKEN_STRING']

class InMemoryTokenProvider(TokenProvider):
    def __init__(self, userToken, urlToken):
        self.userToken = userToken
        self.urlToken = urlToken

    def getUserToken(self):
        return self.userToken

    def getUrlToken(self):
        return self.urlToken

class ConfigurationProvider:
    __metaclass__ = ABCMeta

    @abstractmethod
    def getConfiguration(self):
        pass

class JsonFileConfigurationProvider(ConfigurationProvider):
    def __init__(self, filename):
        self.filename = filename

    def getConfiguration(self):
        with open(self.filename, 'r') as f:
            return json.load(f)

class InMemoryConfigurationProvider(ConfigurationProvider):
    def __init__(self, configuration):
        self.setConfiguration(configuration)

    def setConfiguration(self, configuration):
        self.configuration = configuration

    def updateConfiguration(self, updates):
        self.configuration.update(updates)

    def getConfiguration(self):
        return self.configuration

