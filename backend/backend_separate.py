from tornado.web import StaticFileHandler, RequestHandler, Application as TornadoApplication
from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop, PeriodicCallback
from os.path import dirname, join as join_path
from json import dumps as dumps_json, loads as loads_json
from threading import Thread, ThreadError
from time import sleep
import numpy as np
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
import sys
from datetime import datetime, time

db_foler_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db'))

# Add db_foler_path to sys.path
sys.path.insert(0, db_foler_path)
from db import SensorData, Teams


load_dotenv()
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST", "localhost")
db_name = os.getenv("DB_NAME")
connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}"
print(f"Connection string: {connection_string} \n" )
engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}")

SessionLocal = sessionmaker(bind=engine)

def extract_teams_dict() ->dict[int:str]:
    session = SessionLocal()
    teams = session.query(Teams).all()
    teams_dict = dict()
    for team in teams:
        teams_dict[team.id] = team.name
    # print(teams_ids)    
    session.close()
    return teams_dict

class GraphDataHandler(RequestHandler):
    def get(self):
        # Create a new session
        session = SessionLocal()

        try:
            # Fetch all data, ordered by team_id and timestamp
            query = (
                session.query(SensorData)
                .order_by(SensorData.team_id, SensorData.timestamp)  # Order by team_id and timestamp
            )

            # Get all the data for all teams
            all_data = query.all()

            # Organize the data by team_id for easier frontend consumption
            result = {}
            for data in all_data:
                if data.team_id not in result:
                    result[data.team_id] = []

                result[data.team_id].append({
                    'timestamp': data.timestamp.isoformat(),  # ISO format for date-time
                    'temperature': data.temperature,
                    'humidity': data.humidity if data.humidity is not None else None,
                    'illumination': data.illumination if data.illumination is not None else None
                })

            # Respond with JSON data, structure is { 'team_id': [data] }
            # print(result)

            restructured_data = self.restructure_data(result)
            averages = self.calculate_hourly_averages(restructured_data)
            print(averages)
            self.set_header("Content-Type", "application/json")
            self.write(dumps_json(averages))

        except Exception as e:
            # Handle any errors during the data fetch
            self.set_status(500)
            self.write({"error": str(e)})

        finally:
            # Close the session
            session.close()
    
    def calculate_hourly_averages(self, data):
        averages = {}
        for timestamp, readings in data.items():
            team_data = {}

            for record in readings:
                team_id = record['team_id']
                if team_id not in team_data:
                    team_data[team_id] = {'temp': [], 'humi': [], 'illu': []}
                
                if record['temp'] is not None:
                    team_data[team_id]['temp'].append(record['temp'])
                if record['humi'] is not None:
                    team_data[team_id]['humi'].append(record['humi'])
                if record['illu'] is not None:
                    team_data[team_id]['illu'].append(record['illu'])

            averages[timestamp] = []
            for team_id, metrics in team_data.items():
                avg_temp = sum(metrics['temp']) / len(metrics['temp']) if metrics['temp'] else None
                avg_humi = sum(metrics['humi']) / len(metrics['humi']) if metrics['humi'] else None
                avg_illu = sum(metrics['illu']) / len(metrics['illu']) if metrics['illu'] else None

                averages[timestamp].append({
                    'team_id': team_id,
                    'mean_temp': avg_temp,
                    'mean_humi': avg_humi,
                    'mean_illu': avg_illu
                })

        return averages

    def restructure_data(self, data:dict[int:list[dict]]) -> dict:
        timestamp_dict = {}
        timestamp_dict = self.fill_dict_with_timestamp_keys(timestamp_dict, data)
        # timestamp_dict = timestamp_dict.copy()
        for team_id, _list in data.items():
            for record in _list:
                timestamp_string = record.get('timestamp')
                timestamp_key = self.key_based_on_time_string(timestamp_string)
                temp = record.get('temperature')
                humi = record.get('humidity')
                illu = record.get('illumination')
                timestamp_dict[timestamp_key].append(
                    {
                        'team_id' : team_id,
                        'temp' : temp,
                        'humi' : humi,
                        'illu' : illu
                    }
                )
        
        return timestamp_dict
    

    def key_based_on_time_string(self, timestamp:str)->str:
        dt = datetime.fromisoformat(timestamp)
        date = dt.date()
        hour = dt.hour
        timestamp_key = datetime.combine(date, time(hour))
        return timestamp_key.isoformat()

    def fill_dict_with_timestamp_keys(self, timestamp_dict:dict, data:dict):
        for team_id, _list in data.items():
            for record in _list:
                timestamp_string = record.get('timestamp')
                timestamp_key = self.key_based_on_time_string(timestamp_string)
                if timestamp_key in timestamp_dict:
                    continue
                else:
                    timestamp_dict[timestamp_key] = []
        return timestamp_dict

    
        

class LatestDataHandler(RequestHandler): # zaručuje loadovani dat pri refreshi
    def get(self) -> None:
        # Fetch the most recent data for each team (or however you aggregate it)
        latest_data = self.application.fetch_sensor_data()
        self.write({"sensor_data": latest_data})
        
    
class MainHandler(RequestHandler):
    def get(self) -> None:  
        # self.render("static/index_css_js_ws.html")
        self.render("static/index.html")
        


class WSHandler(WebSocketHandler):

    def initialize(self) -> None:
        self.application.ws_clients.append(self)
        print('Webserver: New WS Client. Connected clients:', len(self.application.ws_clients))

    def open(self)  -> None:
        print('Webserver: Websocket opened.')
        self.write_message('Server ready.')

    def on_message(self, msg)  -> None:
        try:
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
        print('Webserver: Websocket client closed. Connected clients:', len(self.application.ws_clients))

class WebWSApp(TornadoApplication):

    def __init__(self):
        self.ws_clients = []
        self.counter = 0

        self.tornado_handlers = [
            (r'/', MainHandler),
            (r"/graph-data", GraphDataHandler),
            (r'/websocket', WSHandler),
            (r'/latest-data', LatestDataHandler), 
            (r'/graphs', GraphsHandler),
            (r'/(.*)', StaticFileHandler, {'path': join_path(dirname(__file__), 'static')})
        ]
        self.tornado_settings = {
            "debug": True,
            "autoreload": True
        }
        # Periodically fetch and broadcast sensor data to WebSocket clients
        self.periodic_fetch = PeriodicCallback(self.fetch_and_broadcast_data, 5000  )  # 5000ms = 5 seconds
        self.periodic_fetch.start()

        TornadoApplication.__init__(self, self.tornado_handlers, **self.tornado_settings)
        ####
        # self.incrementer = PeriodicCallback(self.increment_and_broadcast, 1000)  # Every 1000ms (1 second)
        # self.incrementer.start()
        #### Toto fungovalo, od chatbota

    def fetch_sensor_data(self) -> list:
            """Fetches the latest sensor data from the database"""
            session = SessionLocal()
            try:
                # Query the sensor_data; filter by team_id if specified
                subquery = (
                    session.query(
                        SensorData.team_id,
                        func.max(SensorData.timestamp).label("latest_timestamp")
                    )
                    .group_by(SensorData.team_id)
                    .subquery()
                )

                query = (
                    session.query(SensorData)
                    .join(subquery, (SensorData.team_id == subquery.c.team_id) & (SensorData.timestamp == subquery.c.latest_timestamp))
                )
                
                data = query.all()
                
                # Convert query result to a list of dictionaries for JSON serialization
                sensor_data_list = [
                    {
                        "id": d.id,
                        "team_id": d.team_id,
                        "team_name": team_dict[d.team_id],
                        "timestamp": d.timestamp.isoformat(),
                        "temperature": d.temperature,
                        "humidity": d.humidity,
                        "illumination": d.illumination
                    }
                    for d in data
                ]
                # print(sensor_data_list)
                return sensor_data_list

            finally:
                session.close()

    def fetch_and_broadcast_data(self) -> None:
        """Fetches all sensor data and broadcasts to all connected WebSocket clients."""
        # print("Fetching latest sensor data for broadcast.")
        sensor_data = self.fetch_sensor_data()  # Fetch all data; can be modified to fetch specific teams
        message = {"sensor_data": sensor_data}
        self.send_ws_message(message)

    def send_ws_message(self, message) -> None:
        for client in self.ws_clients:
            iol.spawn_callback(client.write_message, dumps_json(message))

    # def increment_and_broadcast(self): 
    #     # sleep(5)
    #     print("incremention initialized")
    #     for _ in range(1000):
    #         sleep(1)
    #         self.counter += 1 
    #         print("Counter:", int(self.counter))
    #         self.send_ws_message({"counter": int(self.counter)})


class GraphsHandler(RequestHandler):
    def get(self) -> None:
        self.render("static/graphs.html")



if __name__ == '__main__':
    PORT = 8881
    app = WebWSApp()
    print('Webserver: Initialized. Listening on', PORT)
    team_dict = extract_teams_dict()
    print(team_dict)
    app.listen(PORT)
    iol = IOLoop.current()
    iol.start()
    
