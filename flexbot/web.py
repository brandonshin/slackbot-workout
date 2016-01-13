import cherrypy
import logging
import pystache
import random

from constants import Constants
from util import StatementRenderer

class FlexbotWebServer(object):
    SUCCESS_STATEMENTS = [
        "Awesome job, {}! Keep up the good work.",
        "Fantastic work, {}!",
        "Took you long enough... :wink:",
        ":weight_lifter:"
    ]

    FAILURE_STATEMENTS = [
        "Way to jump the gun, Sparky",
        "I know you're excited, but you can't take credit for someone else's exercise!"
    ]

    CHARS_TO_IGNORE = "!"

    def __init__(self, user_manager, ack_handler, configuration):
        self.user_manager = user_manager
        self.ack_handler = ack_handler
        self.configuration = configuration
        self.logger = logging.getLogger(__name__)

    @cherrypy.expose
    def index(self):
        return "Welcome to {}'s webserver!".format(self.configuration.bot_name())

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def flex(self, **args):
        user_id = args['user_id']
        text = args['text'].lower()
        for char in self.CHARS_TO_IGNORE:
            text = text.replace(char, "")
        if user_id != "USLACKBOT" and text.startswith(self.configuration.bot_name().lower()):
            self.logger.debug('message: %s', args['text'])
            response = self.handle_message(text, user_id)
            if response is not None:
                self.logger.debug('response: %s', response['text'])
            return response

    def handle_message(self, text, user_id):
        args = text.split()[1:]
        command = args[0]
        if command == "help":
            return self.print_help()
        elif command == "exercises":
            return self.print_exercises()
        elif command == "info":
            return self.print_exercise_info(" ".join(args[1:]))
        elif command == "stats":
            return self.print_stats(user_id, args[1:])
        elif self.configuration.enable_acknowledgment() and command == "done":
            return self.acknowledge_winner(user_id)
        elif self.configuration.enable_acknowledgment() and command == "todo":
            return self.print_assignments()
        elif command == "reload":
            return self.reload_configuration()
        else:
            return self.cant_parse_message()

    def print_help(self):
        template_options = {
            'channel_name': self.configuration.channel_name(),
            'bot_name': self.configuration.bot_name(),
            'enable_acknowledgment': self.configuration.enable_acknowledgment()
        }
        helptext = pystache.render("""\
Welcome to {{channel_name}}! I am {{bot_name}}, your friendly helpful workout bot. Here are a couple useful commands you can use to talk with me:
- `{{bot_name}} help`: print this help message
- `{{bot_name}} exercises`: print the exercises that I can announce
- `{{bot_name}} info <EXERCISE>`: print a short informational blob on how to do `EXERCISE` correctly
- `{{bot_name}} stats [user1 [user2 [...]]]`: print the stats for user1, user2, ... If no user is provided, prints the stats for the requesting user
- `{{bot_name}} stats channel`: print the stats for everyone in the channel
{{#enable_acknowledgment}}
- `{{bot_name}} done`: indicate that you have indeed finished your exercise for the current round
- `{{bot_name}} todo`: show users who have a pending exercise and the exercise they must do
{{/enable_acknowledgment}}
- `{{bot_name}}, I don't have to listen to you`: doubles your exercise quota permanently (coming soon)
{{#enable_acknowledgment}}

A little primer on how I work: after I call you out for an exercise, I will only log your workout after you let me know that you have finished your assigned exercise by sending `{{bot_name}} done` to the channel. Otherwise, your workout will go unrecorded!
{{/enable_acknowledgment}}
""", template_options)
        return {'text': helptext}

    def print_exercises(self):
        exercises_text = "The currently supported exercises are: "
        exercises_text += ", ".join(map(lambda e: e.name, self.configuration.exercises()))
        return {'text': exercises_text}

    def print_exercise_info(self, exercise_name):
        exercise_reverse_lookup = {}
        for exercise in self.configuration.exercises():
            exercise_reverse_lookup[exercise.name] = exercise
        if exercise_name in exercise_reverse_lookup:
            exercise = exercise_reverse_lookup[exercise_name]
            exercise_info = "{} description: {}".format(exercise.name, exercise.info)
            return {'text': exercise_info}
        else:
            return {'text': 'I don\'t recognize that exercise...'}

    def print_stats(self, current_user_id, usernames):
        user_reverse_lookup = {}
        users_to_print = set()
        if len(usernames) == 0:
            users_to_print.add(current_user_id)
        else:
            for user_id in self.user_manager.users:
                user = self.user_manager.users[user_id]
                user_reverse_lookup[user.username.lower()] = user_id
            for username in usernames:
                self.logger.debug("Looking up username %s", username)
                username = username[1:] if username.startswith("@") else username
                if username in user_reverse_lookup:
                    users_to_print.add(user_reverse_lookup[username])
                elif username == "channel":
                    users_to_print = self.user_manager.users.keys()
                    break
        if len(users_to_print) > 0:
            stats = self.user_manager.stats(list(users_to_print))
            return {
                "text": stats
            }

    def acknowledge_winner(self, user_id):
        result = self.ack_handler.acknowledge_winner(user_id)
        if result == Constants.ACKNOWLEDGE_SUCCEEDED:
            return self.acknowledge_success(user_id)
        elif result == Constants.ACKNOWLEDGE_FAILED:
            return self.acknowledge_failure(user_id)

    def _acknowledge_winner(self, user_id, statements_list):
        statement = random.choice(statements_list)
        username = self.user_manager.get_firstname(user_id)
        if username == '':
            username = self.user_manager.get_username(user_id)
        rendered_statement = StatementRenderer(statement).render_statement(username)
        return {'text': rendered_statement}

    def acknowledge_success(self, user_id):
        return self._acknowledge_winner(user_id, self.SUCCESS_STATEMENTS)

    def acknowledge_failure(self, user_id):
        return self._acknowledge_winner(user_id, self.FAILURE_STATEMENTS)

    def print_assignments(self):
        response = ''
        current_winners = self.user_manager.get_current_winners()
        if len(current_winners) == 0:
            response = 'No pending exercises. Keep on working out!'
        else:
            # Write to the command console today's breakdown
            response = "```\n"
            #s += "Username\tAssigned\tComplete\tPercent
            response += "Username".ljust(15)
            response += "Exercise"
            response += "\n---------------------------------------------------------------\n"
            for user_id, exercise, reps in current_winners:
                response += self.user_manager.get_username(user_id).ljust(15)
                response += "{} {} {}".format(reps, exercise.units, exercise.name)
                response += "\n"

            response += "```"
        return {'text': response}


    def reload_configuration(self):
        self.configuration.set_configuration()

    def cant_parse_message(self):
        # alternatively respond with an error message here
        pass
