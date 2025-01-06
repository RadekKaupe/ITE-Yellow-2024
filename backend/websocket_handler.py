
import json
from urllib.parse import urlencode
from psycopg2 import IntegrityError
import psycopg2
import tornado
from tornado.web import StaticFileHandler, RequestHandler, Application as TornadoApplication
from tornado.web import RedirectHandler
from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop, PeriodicCallback
from os.path import dirname, join as join_path
from json import dumps as dumps_json, loads as loads_json
from threading import Thread, ThreadError
from time import sleep
class WSHandler(WebSocketHandler):
    """Handles some WebSocket Communication, not really used."""

    def initialize(self) -> None:
        self.application.ws_clients.append(self)
        print('Webserver: New WS Client. Connected clients:',
              len(self.application.ws_clients))

    def open(self) -> None:
        print('Webserver: Websocket opened.')
        self.write_message('Server ready.')

    def on_message(self, msg) -> None:
        try:
            print(msg)
            msg = loads_json(msg)
            print('Webserver: Received json WS message:', msg)

            # If 'team_id' is sent, we can send the specific data immediately as well
            if 'team_id' in msg:
                team_data = self.application.fetch_sensor_data(msg['team_id'])
                self.write_message(dumps_json({"sensor_data": team_data}))
        except ValueError:
            print('Webserver: Received WS message:', msg)

    def on_close(self) -> None:
        self.application.ws_clients.remove(self)
        print('Webserver: Websocket client closed. Connected clients:',
              len(self.application.ws_clients))
        
    @staticmethod 
    def send_message(self, message): 
        for client in self.application.ws_clients: client.write_message(message)