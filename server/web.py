import cherrypy

class FlexbotWebServer(object):
    def __init__(self, user_manager):
        self.user_manager = user_manager

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        posted_text = cherrypy.request.json["text"]
        return {
            "text": posted_text
        }
