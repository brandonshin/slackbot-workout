import cherrypy

class FlexbotWebServer(object):
    def __init__(self, user_manager):
        self.user_manager = user_manager

    @cherrypy.expose
    def index(self):
        return "Welcome to flexbot's webserver!"

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def flex(self):
        posted_text = cherrypy.request.json["text"]
        print posted_text
        return {
            "text": posted_text
        }
