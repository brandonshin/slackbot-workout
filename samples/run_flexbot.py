import argparse
import json
import logging
import logging.config
import yaml

from flexbot.configurators import JsonFileConfigurationProvider, YamlFileConfigurationProvider
from flexbot.server import Server

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.yaml",
            help="Configuration file path (can be JSON or YAML)")
    parser.add_argument("-l", "--logging-config", default="logging.yaml",
            help="Logging configuration file path (can be JSON or YAML)")
    args = parser.parse_args()
    with open(args.logging_config, 'r') as f:
        if args.logging_config.endswith(".yaml"):
            logging.config.dictConfig(yaml.load(f))
        elif args.logging_config.endswith(".json"):
            logging.config.dictConfig(json.load(f))
        else:
            raise Exception("Logging configuration path must end with .yaml or .json")

    config = None
    if args.config.endswith(".yaml"):
        config = YamlFileConfigurationProvider(args.config)
    elif args.config.endswith(".json"):
        config = JsonFileConfigurationProvider(args.config)
    else:
        raise Exception("Configuration path must end with .yaml or .json")

    server = Server(config)
    server.start()

if __name__ == "__main__":
    main()
