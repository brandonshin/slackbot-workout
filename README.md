# slackbot-workout
A fun hack that gets Slackbot to force your teammates to work out!

<img src = "https://ctrlla-blog.s3.amazonaws.com/2015/Jun/Screen_Shot_2015_06_10_at_5_57_55_PM-1433984292189.png" width = 500>


# Instructions

1. Clone the repo and navigate into the directory in your terminal.

    `$ git clone git@github.com:brandonshin/slackbot-workout.git`

2. Go to your slack home page [https://{yourgroup}.slack.com/home](http://my.slack.com/home) & click on **Integrations** on the left sidebar.

    <img src = "https://ctrlla-blog.s3.amazonaws.com/2015/Jun/Screen_Shot_2015_06_05_at_7_21_33_PM-1433557303531.png" width = 300>

3. Scroll All the Way Down until you see **Slack API** and **Slackbot**. You'll need to access these two integrations.

    <img src="https://ctrlla-blog.s3.amazonaws.com/2015/Jun/Screen_Shot_2015_06_05_at_7_19_44_PM-1433557206307.png" width = 500>

4. In the **Slack API Page**, select **WebAPI** in the left side bar, scroll all the way down, and register yourself an auth token. You should see this. Take note of the token, e.g. `xoxp-2751727432-4028172038-5281317294-3c46b1`. This is your **User Auth Token**

    <img src="https://ctrlla-blog.s3.amazonaws.com/2015/Jun/Screen_Shot_2015_06_05_at_7_00_24_PM-1433557433415.png" width = 500>

5. In the **Slackbot** (Remote control page). Register an integration & you should see this. __Make sure you grab just the token out of the url__, e.g. `AizJbQ24l38ai4DlQD9yFELb`

    <img src="https://ctrlla-blog.s3.amazonaws.com/2015/Jun/Screen_Shot_2015_06_03_at_8_44_00_AM-1433557565175.png" width = 500>

6. Copy the `default.json` file to `config.json` ( `cp default.json config.json` )

6. Save your user token and url token in the `config.json` file you just copied.


    Open `config.json` and set `teamDomain` (ex: ctrlla) `channelName` (ex: general) and `channelId` (ex: B22D35YMS).
    Set any other configurations as you like.

    If you don't know the channel Id, fetch it using

    `$ python fetchChannelId.py channelname`

7. If you haven't set up pip for python, go in your terminal and run.
`$ sudo easy_install pip`

8. While in the project directory, run

    `$ sudo pip install -r requirements.txt`

    `$ python slackbotExercise.py`

Run the script to start the workouts and hit ctrl+c to stop the script. Hope you have fun with it!

## Docker

This project includes a Dockerfile that will run the python script within a container.

To run the Docker container, follow these steps:

#### Pull the container

```sh
$ docker pull slackbots/exercise
```

#### Run the container

This container expects a config file somewhere in its file system. The easiest
way to do this, is to mount a directory on the host, inside of the container. We
do this using the `-v` flag when running the container.

The example we give is `-v "$PWD:/slackbot"`, Where `$PWD` is the current direcotry
you're mounting. Just make sure you have a JSON config file in it.

After that, you'll need to set an environment variable when running the
container to point to the configuration file.

```sh
$ docker run -t -v "$PWD:/slackbot" -e "CONFIG_FILE=/slackbot/config.json" slackbots/exercise
```
