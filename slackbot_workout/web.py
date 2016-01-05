import cherrypy
import logging
import pystache

class FlexbotWebServer(object):
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
        self.logger.debug('message: %s'.format(args['text']))
        text = args['text'].lower()
        if user_id != "USLACKBOT" and text.startswith(self.configuration.bot_name().lower()):
            response = self.handle_message(text, user_id)
            if response is not None:
                self.logger.debug('response: %s'.format(response['text']))
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
            return self.print_stats(args[1:])
        elif self.configuration.enable_acknowledgment() and command == "done":
            return self.acknowledge_winner(user_id)
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
- `{{bot_name}} stats user1 [user2 [...]]`: print the stats for user1, user2, ...
- `{{bot_name}} stats channel`: print the stats for everyone in the channel
{{#enable_acknowledgment}}
- `{{bot_name}} done`: indicate that you have indeed finished your exercise for the current round
{{/enable_acknowledgment}}
- `{{bot_name}}, I don't have to listen to you`: doubles your exercise quota permanently (coming soon)
{{#enable_acknowledgment}}

A little primer on how I work: after I call you out for an exercise, I will only log your workout after you let me know that you have finished your assigned exercise by sending `{bot_name} done` to the channel. Otherwise, your workout will go unrecorded!
{{/enable_acknowledgment}}
""", template_options)
        return {'text': helptext}

    def print_exercises(self):
        exercises_text = "The currently supported exercises are: "
        exercises_text += ", ".join(map(lambda e: e['name'], self.configuration.exercises()))
        return {'text': exercises_text}

    def print_exercise_info(self, exercise_name):
        exercise_reverse_lookup = {}
        for exercise in self.configuration.exercises():
            exercise_reverse_lookup[exercise['name']] = exercise
        if exercise_name in exercise_reverse_lookup:
            exercise = exercise_reverse_lookup[exercise_name]
            exercise_info = "{} description: {}".format(exercise['name'], exercise['info'])
            return {'text': exercise_info}
        else:
            return {'text': 'I don\'t recognize that exercise...'}

    def print_stats(self, usernames):
        user_reverse_lookup = {}
        users_to_print = set()
        for user_id in self.user_manager.users:
            user = self.user_manager.users[user_id]
            user_reverse_lookup[user.username.lower()] = user_id
            user_reverse_lookup[user.real_name.lower()] = user_id
        for username in usernames:
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
        self.ack_handler.acknowledge_winner(user_id)

    def reload_configuration(self):
        self.configuration.set_configuration()

    def cant_parse_message(self):
        # alternatively respond with an error message here
        pass
