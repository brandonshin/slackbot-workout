import cherrypy

class FlexbotWebServer(object):
    def __init__(self, user_manager, configuration):
        self.user_manager = user_manager
        self.configuration = configuration
        config_json = configuration.get_configuration()
        self.bot_name = config_json['botName'].lower()

    @cherrypy.expose
    def index(self):
        return "Welcome to flexbot's webserver!"

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def flex(self, **args):
        user_id = args['user_id']
        text = args['text'].lower()
        if user_id != "USLACKBOT" and self.bot_name in text:
            words = text.split()
            user_reverse_lookup = {}
            users_to_print = []
            for user_id in self.user_manager.users:
                user = self.user_manager.users[user_id]
                user_reverse_lookup[user.username.lower()] = user_id
                user_reverse_lookup[user.real_name.lower()] = user_id
            for word in words:
                if word in user_reverse_lookup:
                    users_to_print.append(user_reverse_lookup[word])
                elif word == "channel" or word == "@channel":
                    users_to_print = self.user_manager.users.keys()
                    break
            if len(users_to_print) > 0:
                stats = self.user_manager.stats(list(set(users_to_print)))
                return {
                    "text": stats
                }


