from tornado.web import StaticFileHandler, RequestHandler, Application as TornadoApplication
from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop, PeriodicCallback
from os.path import dirname, join as join_path
from json import dumps as dumps_json, loads as loads_json
from threading import Thread, ThreadError
from time import sleep
import numpy as np

class MainHandler(RequestHandler):
    def get(self):  
        # self.render("static/index_css_js_ws.html")
        self.render("static/index.html")


class WSHandler(WebSocketHandler):

    def initialize(self):
        self.application.ws_clients.append(self)
        print('Webserver: New WS Client. Connected clients:', len(self.application.ws_clients))

    def open(self):
        print('Webserver: Websocket opened.')
        self.write_message('Server ready.')

    def on_message(self, msg):
        try:
            msg = loads_json(msg)
            print('Webserver: Received json WS message:', msg)
        except (ValueError):
            print('Webserver: Received WS message:', msg)

    def on_close(self):
        self.application.ws_clients.remove(self)
        print('Webserver: Websocket client closed. Connected clients:', len(self.application.ws_clients))

class WebWSApp(TornadoApplication):

    def __init__(self):
        self.ws_clients = []
        self.counter = 0

        self.tornado_handlers = [
            (r'/', MainHandler),
            (r'/websocket', WSHandler),
            (r'/(.*)', StaticFileHandler, {'path': join_path(dirname(__file__), 'static')})
        ]
        self.tornado_settings = {
            "debug": True,
            "autoreload": True
        }
        try:
            t = Thread(target=self.increment_and_broadcast,daemon=True)
            t.start()
        except ThreadError:
            print('ERR: Thread Websocket')




        TornadoApplication.__init__(self, self.tornado_handlers, **self.tornado_settings)
        ####
        # self.incrementer = PeriodicCallback(self.increment_and_broadcast, 1000)  # Every 1000ms (1 second)
        # self.incrementer.start()
        #### Toto fungovalo, od chatbota


    def send_ws_message(self, message):
        for client in self.ws_clients:
            iol.spawn_callback(client.write_message, dumps_json(message))

    def increment_and_broadcast(self): 
        # sleep(5)
        print("incremention initialized")
        for _ in range(1000):
            sleep(1)
            self.counter += 1 
            print("Counter:", int(self.counter))
            self.send_ws_message({"counter": int(self.counter)})


if __name__ == '__main__':
    PORT = 8881
    app = WebWSApp()
    print('Webserver: Initialized. Listening on', PORT)
    app.listen(PORT)
    iol = IOLoop.current()
    iol.start()
    
