# slackbot-workout
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

5. Save your `SLACK_USER_TOKEN_STRING` as environmental variables in your terminal.

    ```
    $ export SLACK_USER_TOKEN_STRING=YOURUSERTOKEN
    ```

    Alternatively, if you're using the `InMemoryTokenConfigurator` you can provide the token within
    the Python program itself.

6. Set up channel and customize configurations

    Open `config.json` and set `teamDomain` (ex: ctrlla) and `channelName` (ex: general). Set any other configurations as you like.

7. While in the project directory, run

    ```
    $ sudo ./install-dependencies.sh
    $ sudo pip install -r requirements.txt
    $ python sample.py
    ```

    Run the script to start the workouts and hit ctrl+\ to stop the script. Hope you have fun with it!
