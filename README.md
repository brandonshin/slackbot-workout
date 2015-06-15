# slackbot-workout
A fun hack that gets Slackbot to force your teammates to work out!

<img src = "https://ctrlla-blog.s3.amazonaws.com/2015/Jun/Screen_Shot_2015_06_10_at_5_57_55_PM-1433984292189.png" width = 500>

# Run it on Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy)

# Instructions

1. Clone the repo and navigate into the directory in your terminal.

    `$ git clone git@github.com:brandonshin/slackbot-workout.git`

2. Go to your slack home page [https://{yourgroup}.slack.com/home](http://my.slack.com/home) & click on **Integrations** on the left sidebar.

    <img src = "https://ctrlla-blog.s3.amazonaws.com/2015/Jun/Screen_Shot_2015_06_05_at_7_21_33_PM-1433557303531.png" width = 300>

3. Scroll All the Way Down until you see **Slack API** and **Slackbot**. You'll need to access these two integrations.

    <img src="https://ctrlla-blog.s3.amazonaws.com/2015/Jun/Screen_Shot_2015_06_05_at_7_19_44_PM-1433557206307.png" width = 500>

4. In the **Slack API Page**, select **WebAPI** in the left side bar, scroll all the way down, and register yourself an auth token. You should see this. Take note of that token, e.g. `xoxp-2751727432-4028172038-5281317294-3c46b1`. That's your **User Auth Token**

    <img src="https://ctrlla-blog.s3.amazonaws.com/2015/Jun/Screen_Shot_2015_06_05_at_7_00_24_PM-1433557433415.png" width = 500>

5. In the **Slackbot** (Remote control page). Register an integration & you should see this. __Make sure you grab just the token out of the url__, e.g. `AizJbQ24l38ai4DlQD9yFELb`

    <img src="https://ctrlla-blog.s3.amazonaws.com/2015/Jun/Screen_Shot_2015_06_03_at_8_44_00_AM-1433557565175.png" width = 500>


6. In a terminal export the variables you collected earlier

    `$ export SLACK_USER_TOKEN=xxxx-yyyy-12345`

    `$ export SLACK_URL_TOKEN=tokenonly`

    `$ export SLACK_TEAM_NAME='slackteam'`

    `$ export SLACK_CHANNEL='testing'`

8. While in the project directory, run

    `$ make run`

Hit ctrl+c to stop the script. Hope you have fun with it!
