# slackbot-workout
[![Build Status](https://travis-ci.org/mgyucht/slackbot-workout.svg?branch=hackathon)](https://travis-ci.org/mgyucht/slackbot-workout)

A fun hack that gets Slackbot to force your teammates to work out!

<img src = "https://ctrlla-blog.s3.amazonaws.com/2015/Jun/Screen_Shot_2015_06_10_at_5_57_55_PM-1433984292189.png" width = 500>

# Instructions

1. Clone the repo and navigate into the directory in your terminal.

    `$ git clone git@github.com:mgyucht/slackbot-workout.git`

2. Go to your slack home page [https://{yourgroup}.slack.com/home](http://my.slack.com/home) & click on **Integrations** on the left sidebar.

    <img src = "https://ctrlla-blog.s3.amazonaws.com/2015/Jun/Screen_Shot_2015_06_05_at_7_21_33_PM-1433557303531.png" width = 300>

3. Scroll All the Way Down until you see **Slack API** and **Slackbot**. You'll need to access these two integrations.

    <img src="https://ctrlla-blog.s3.amazonaws.com/2015/Jun/Screen_Shot_2015_06_05_at_7_19_44_PM-1433557206307.png" width = 500>

4. In the **Slack API Page**, select **WebAPI** in the left side bar, scroll all the way down, and register yourself an auth token. You should see this. Take note of the token, e.g. `xoxp-2751727432-4028172038-5281317294-3c46b1`. This is your **User Auth Token**

    <img src="https://ctrlla-blog.s3.amazonaws.com/2015/Jun/Screen_Shot_2015_06_05_at_7_00_24_PM-1433557433415.png" width = 500>

5. Set up channel and customize configurations

    Copy `default.yaml` or `default.json` and configure to your heart's desire. There are a handful of sample configurations located in the `samples/` directory.

6. While in the project directory, run

    ```
    $ sudo ./install-dependencies.sh
    $ sudo pip install -r requirements.txt
    $ python -m samples.flexbot
    ```

    Run the script to start the workouts and hit ctrl+\ to stop the script. Hope you have fun with it!

# Docker usage

Alternatively to running the source directly, my [Docker hub page for flexbot](https://hub.docker.com/r/yucht/flexbot/) is linked to the current version on the `hackathon` branch. This should simplify the setup substantially. In order to run this docker container, you need to bind mount the configuration and logging configuration into the `/flexbot/configuration` directory in the container. Additionally, you'll need to set up the port mapping for whatever port you have specified the web server to run on.

1. Run `docker pull yucht/flexbot:latest` to get the most recent version from the registry.
2. Run 

   ```
   docker run -v <config_file>:/flexbot/configuration/config.yaml \
       -v <logging_config_file>:/flexbot/configuration/logging.yaml \
       -d -p 80:80 -t yucht/flexbot:latest
   ```

   where <config_file> is your flexbot configuration and <logging_config_file> is your logging
   configuration to start running flexbot.

To ease development, this docker container also exposes port 8080, so if you want to run a development version for testing and a production version simultaneously, you can simply bring up your webserver on port 8080 and run a production container and a development one simultaneously.

# Usage

Currently, you can specify two configuration files, one which controls the behavior of slackbot, and the other which controls the behavior of the loggers in slackbot. The `samples.flexbot` module currently defaults to using `config.yaml` and `logging.yaml` in the current working directory, but you can specify alternate configuration files by using `--config` and `--logging-config` respectively. Slackbot can read both YAML and JSON files for the configuration files and exercise files.
