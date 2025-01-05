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
import numpy as np
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.orm import sessionmaker, Session, aliased
import sys
from datetime import datetime, time, timedelta
import pytz
from datetime import datetime, timezone
from tornado.web import HTTPError
import jwt
import bcrypt
from psycopg2.errors import UniqueViolation
# Import of db.py for classes, which are the columns in the database tables
db_foler_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'db'))

sys.path.insert(0, db_foler_path)
from db import SensorData, Teams, SensorDataOutliers 

# Connecting to the database
load_dotenv()
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST", "localhost")
db_name = os.getenv("DB_NAME")
connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}"
print(f"Connection string: {connection_string} \n")
engine = create_engine(
    f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}")
LOCAL_TIMEZONE = pytz.timezone("Europe/Prague")

SessionLocal = sessionmaker(bind=engine)

from auth import LoginHandler, RegisterHandler, LogoutHandler, BaseHandler, ReceiveImageHandler, RecognizeImageHandler, TrainingHandler

def convert_to_local_time(utc_timestamp: str):
    """Convert a utc timestamp to the LOCAL_TIMEZONE, which is needed for the testing table in the db"""
    try:
        # Attempt to parse with fractional seconds
        utc_time = datetime.strptime(utc_timestamp, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        try:
            # Attempt to parse without fractional seconds
            utc_time = datetime.strptime(utc_timestamp, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            # If neither format matches, raise an error
            raise ValueError(f"Invalid timestamp format: '{utc_timestamp}'")

    # Set timezone to UTC and convert to local timezone
    utc_time = utc_time.replace(tzinfo=pytz.UTC)
    return utc_time.astimezone(LOCAL_TIMEZONE)


def extract_teams_dict() -> dict[int:str]:
    """Fetches all the team names and team ids from the database itself, for better control and manipulation"""
    session = SessionLocal()
    teams = session.query(Teams).all()
    teams_dict = dict()
    for team in teams:
        teams_dict[team.id] = team.name
    session.close()
    return teams_dict


class GraphDataHandler(BaseHandler):
    """
    This Handler fetches data from the last X days and processes it 

    """

    def get(self):
        """Writes the data into a dummy page, so the front end can fetch it and use it for the graph display"""
        try:
            averages = self.fetch_data(days=1)
            self.set_header("Content-Type", "application/json")
            if averages is not None:
                self.write(dumps_json(averages))
        except Exception as e:
            self.set_status(500)
            self.write({"error": str(e)})

    def fetch_data(self, days: int = 1):
        """
        Connects to the database, fetches data from the last X days and restructures it
        The restrucutred format:

        {
            "timestamp": [
                {
                    "team_id": INT,
                    "mean_temp": FLOAT,
                    "mean_humi": FLOAT,
                    "mean_illu": FLOAT
                },
                {
                    "team_id": INT,
                    "mean_temp": FLOAT,
                    "mean_humi": FLOAT,
                    "mean_illu": FLOAT
                }
            ], ...
            "timestamp": [ 
                {
                    "team_id": INT,
                    "mean_temp": FLOAT,
                    "mean_humi": FLOAT,
                    "mean_illu": FLOAT
                },
                {
                    "team_id": INT,
                    "mean_temp": FLOAT,
                    "mean_humi": FLOAT,
                    "mean_illu": FLOAT
                }
            ], ...            
            "timestamp": [ ... ]

        }

        """
        session = SessionLocal()

        try:
            now = datetime.now()
            time_interval = now - timedelta(days=days)

            # Fetch all data, ordered by team_id and timestamp
            query = (
                session.query(SensorData)
                # Adjust the time range here
                .filter(SensorData.timestamp >= time_interval)
                # Order by team_id and timestamp
                .order_by(SensorData.team_id, SensorData.timestamp)
            )

            # Get all the data for all teams
            all_data = query.all()

            # Organize the data by team_id for easier frontend consumption
            result = {}
            for data in all_data:
                if data.team_id not in result:
                    result[data.team_id] = []
                converted_timestamp = convert_to_local_time(
                    data.timestamp.isoformat()).isoformat()
                # print(converted_timestamp)
                result[data.team_id].append({
                    'timestamp': converted_timestamp,  # ISO format for date-time
                    'temperature': data.temperature,
                    'humidity': data.humidity if data.humidity is not None else None,
                    'illumination': data.illumination if data.illumination is not None else None
                })

            restructured_data = self.restructure_data(result)
            print(restructured_data)
            averages = self.calculate_averages(restructured_data)
            self.set_header("Content-Type", "application/json")
            # self.write(dumps_json(averages))
            return averages

        except Exception as e:
            # Handle any errors during the data fetch
            self.set_status(500)
            self.write({"error": str(e)})

        finally:
            # Close the session
            session.close()

    def calculate_averages(self, data):
        """
        This data calculates the averages for the time interval of one hour
        the timestamp that it returns is a string: "YYYY-MM-DDTXX:00:00" where XX are all the calculated hours
        """
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
                avg_temp = sum(
                    metrics['temp']) / len(metrics['temp']) if metrics['temp'] else None
                avg_humi = sum(
                    metrics['humi']) / len(metrics['humi']) if metrics['humi'] else None
                avg_illu = sum(
                    metrics['illu']) / len(metrics['illu']) if metrics['illu'] else None

                averages[timestamp].append({
                    'team_id': team_id,
                    'mean_temp': avg_temp,
                    'mean_humi': avg_humi,
                    'mean_illu': avg_illu
                })

        return averages

    def restructure_data(self, data: dict[int:list[dict]]) -> dict:
        """
        Restructures the data fetch from the database, into this format:
        {
            "timestamp_key_1": [
                {
                    "team_id": team_id_1,
                    "temp": temp_1,
                    "humi": humi_1,
                    "illu": illu_1
                },
                {
                    "team_id": team_id_2,
                    "temp": temp_2,
                    "humi": humi_2,
                    "illu": illu_2
                },
                # More records for timestamp_key_1
            ],
            "timestamp_key_2": [
                {
                    "team_id": team_id_3,
                    "temp": temp_3,
                    "humi": humi_3,
                    "illu": illu_3
                },
                # More records for timestamp_key_2
            ],
            # More timestamps
        }
        The key has the already mentioned format:"YYYY-MM-DDTXX:00:00" 
        """
        timestamp_dict = {}
        timestamp_dict = self.fill_dict_with_timestamp_keys(
            timestamp_dict, data)
        for team_id, _list in data.items():
            for record in _list:
                timestamp_string = record.get('timestamp')
                timestamp_key = self.key_based_on_time_string(timestamp_string)
                temp = record.get('temperature')
                humi = record.get('humidity')
                illu = record.get('illumination')
                timestamp_dict[timestamp_key].append(
                    {
                        'team_id': team_id,
                        'temp': temp,
                        'humi': humi,
                        'illu': illu
                    }
                )

        return timestamp_dict

    def key_based_on_time_string(self, timestamp: str) -> str:
        """
        Crates the key: "YYYY-MM-DDTXX:00:00" based on the inputed timestamp, so it creates only new one
        """
        dt = datetime.fromisoformat(timestamp)
        date = dt.date()
        hour = dt.hour
        timestamp_key = datetime.combine(date, time(hour))
        return timestamp_key.isoformat()

    def fill_dict_with_timestamp_keys(self, timestamp_dict: dict, data: dict):
        """
        Fills a dictionary with the already mentioned timestamp key, for easier manipulation during the averages calculation
        """
        # Use a set to collect all unique timestamp keys
        timestamp_keys = set()

        for team_id, _list in data.items():
            for record in _list:
                timestamp_string = record.get('timestamp')
                timestamp_key = self.key_based_on_time_string(timestamp_string)
                timestamp_keys.add(timestamp_key)

        # Sort the keys and populate the dictionary in sorted order
        for timestamp_key in sorted(timestamp_keys, key=datetime.fromisoformat):
            if timestamp_key not in timestamp_dict:
                timestamp_dict[timestamp_key] = []

        return timestamp_dict


class GraphsHandler(BaseHandler):
    """Displays the html for one day graphs"""
    @tornado.web.authenticated
    def get(self) -> None:
        self.render("static/graphs_one_day.html")


class GraphData1WeekHandler(GraphDataHandler):
    """

    This Handler fetches data from the last 7 days and processes it 
    It inherits the GraphDataHandler Class and alters some functions a little bit, so the data it returns is like this:

        {
            "date": [
                {
                    "team_id": INT,
                    "mean_temp": FLOAT,
                    "mean_humi": FLOAT,
                    "mean_illu": FLOAT
                },
                {
                    "team_id": INT,
                    "mean_temp": FLOAT,
                    "mean_humi": FLOAT,
                    "mean_illu": FLOAT
                }
            ], ...
            "date": [ 
                {
                    "team_id": INT,
                    "mean_temp": FLOAT,
                    "mean_humi": FLOAT,
                    "mean_illu": FLOAT
                },
                {
                    "team_id": INT,
                    "mean_temp": FLOAT,
                    "mean_humi": FLOAT,
                    "mean_illu": FLOAT
                }
            ], ...            
            "date": [ ... ]

        }
        It's very similiar, but with no time only dates.
        The handler could and probably should be more optimised, right now it still works with data, that is restructured by the Hours of the timestamps, instead of days.
        However, it works and I dont want to break it, so I ain't touching anything.

    """

    def get(self):
        try:
            averages = self.fetch_data(days=7)
            self.set_header("Content-Type", "application/json")
            if averages is not None:
                self.write(dumps_json(averages))
        except Exception as e:
            self.set_status(500)
            self.write({"error": str(e)})

    def calculate_averages(self, data):
        """
        Calculates daily averages, based on the restructured data (which is formated by hours, still)
        the key it returns is the date WITHOUT time: YYYY-MM-DD
        """
        # Dictionary to store intermediate data for averages calculation.
        averages = {}

        # Aggregation loop
        for timestamp, readings in data.items():
            # Extract the date part from the timestamp.
            if "T" in timestamp:
                date = timestamp.split("T")[0]  # ISO 8601 format
            else:
                date = timestamp.split()[0]  # Space-separated format

            if date not in averages:
                # Initialize the date key if not present in averages.
                averages[date] = {}

            for record in readings:
                team_id = record['team_id']

                if team_id not in averages[date]:
                    # Initialize the team data if not present for the current date.
                    averages[date][team_id] = {
                        'temp': [], 'humi': [], 'illu': []}

                # Append the non-None values to the respective lists.
                if record['temp'] is not None:
                    averages[date][team_id]['temp'].append(record['temp'])
                if record['humi'] is not None:
                    averages[date][team_id]['humi'].append(record['humi'])
                if record['illu'] is not None:
                    averages[date][team_id]['illu'].append(record['illu'])

        # Prepare the output with averages.
        daily_averages = {}

        # Average calculation loop
        for date, team_data in averages.items():
            daily_averages[date] = []

            for team_id, metrics in team_data.items():
                # Calculate averages for each metric.
                avg_temp = sum(
                    metrics['temp']) / len(metrics['temp']) if metrics['temp'] else None
                avg_humi = sum(
                    metrics['humi']) / len(metrics['humi']) if metrics['humi'] else None
                avg_illu = sum(
                    metrics['illu']) / len(metrics['illu']) if metrics['illu'] else None

                # Append the team's daily average data to the results for the date.
                daily_averages[date].append({
                    'team_id': team_id,
                    'mean_temp': avg_temp,
                    'mean_humi': avg_humi,
                    'mean_illu': avg_illu
                })

        return daily_averages


class Graphs1WeekHandler(BaseHandler):
    """Renders the weekly graphs webpage"""
    @tornado.web.authenticated
    def get(self):
        self.render("static/graphs_one_week.html")


class AlertDataHandler(BaseHandler):
    """
    Fetches the alert data from the database. It's made to handle multiple teams having alerts, not only one.
    The format:
    {
        "id": <outlier.id>,
        "sensor_data_id": <outlier.sensor_data_id>,
        "team_id": <outlier.sensor_data.team_id>,
        "is_temperature_out_of_range": <outlier.is_temperature_out_of_range>,
        "is_humidity_out_of_range": <outlier.is_humidity_out_of_range>,
        "is_illumination_out_of_range": <outlier.is_illumination_out_of_range>,
        "timestamp": <timestamp> 
    }   
    """

    def get(self):
        # Fetch all the outlier data from the sensor_data_outliers table
        try:
            session = SessionLocal()
            sdo = aliased(SensorDataOutliers)
            sd = aliased(SensorData)
            sdo2 = aliased(SensorDataOutliers)
            sd2 = aliased(SensorData)
            # Create the subquery to find the maximum ID for each team
            subquery = (
                session.query(func.max(sdo2.id))
                .join(SensorData, sdo2.sensor_data_id == SensorData.id)
                .filter(SensorData.team_id == sd.team_id)
                .label("max_id")
            )

            # Main query to select the rows from sensor_data_outliers based on subquery result
            query = (
                session.query(sdo)
                .join(sd, sdo.sensor_data_id == sd.id)
                .filter(sdo.id == subquery)
            )
            latest_alert_data = query.all()
            # Prepare the data to send as JSON response
            outliers_data = [
                {
                    "id": outlier.id,
                    "sensor_data_id": outlier.sensor_data_id,
                    "team_id": outlier.sensor_data.team_id,
                    "is_temperature_out_of_range": outlier.is_temperature_out_of_range,
                    "is_humidity_out_of_range": outlier.is_humidity_out_of_range,
                    "is_illumination_out_of_range": outlier.is_illumination_out_of_range,
                    "timestamp": self.get_timestamp_by_record_id(outlier.sensor_data_id, session)
                }
                for outlier in latest_alert_data
            ]

            # Respond with the list of outliers in JSON format
            self.write({"outliers": outliers_data})
            session.close()
        except Exception as e:
            # Handle any exceptions by sending a 500 error
            self.set_status(500)
            self.write({"error": str(e)})

    def get_timestamp_by_record_id(self, record_id, session) -> str:
        """Fetches a timestamp based on the id and returns it as a string."""
        timestamp = session.query(SensorData.timestamp).filter(
            SensorData.id == record_id).first()
        return timestamp[0].strftime("%Y-%m-%dT%H:%M:%S.%f")


class LatestDataHandler(BaseHandler):
    """This handler fetches the latest data when loading the main page for the first time."""
    def get(self) -> None:
        latest_data = self.application.fetch_sensor_data()
        self.write(latest_data)


class StatisicsHandler(BaseHandler):
    """Renders the statistcs page"""
    @tornado.web.authenticated
    def get(self) -> None:
        self.render("static/statistics.html")


class MainHandler(BaseHandler):
    """Renders the main page."""
    @tornado.web.authenticated
    def get(self) -> None:
        # self.render("static/index_css_js_ws.html")
        self.render("static/index.html")


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


class WebWSApp(TornadoApplication):
    """The main handler. Handles the start of the application as well as sending the data periodically via WebSockets."""

    def __init__(self):
        self.ws_clients = []
        self.counter = 0
        self.tornado_handlers = [
            (r'/', RedirectHandler, {"url": "/login"}),
            (r'/dashboard', MainHandler),
            (r"/graph-data/one-day", GraphDataHandler),
            (r"/graph-data/one-week", GraphData1WeekHandler),
            (r"/alert-data", AlertDataHandler),
            (r'/websocket', WSHandler),
            (r'/latest-data', LatestDataHandler),
            (r'/graphs-one-day', GraphsHandler),
            (r'/graphs-one-week', Graphs1WeekHandler),
            (r'/statistics', StatisicsHandler),
            (r"/login", LoginHandler),
            (r"/register", RegisterHandler),
            (r"/logout", LogoutHandler),
            (r"/receive_image", ReceiveImageHandler),
            (r"/recognize", RecognizeImageHandler),
            (r"/train", TrainingHandler),
            (r'/(.*)', StaticFileHandler,
             {'path': join_path(dirname(__file__), 'static')})
        ]
        self.tornado_settings = {
            "debug": True,
            "autoreload": True,
            "cookie_secret": "your-secret-key",# TODO: add a real secret ke
            "login_url": "/login",
            "secret_key": "your-jwt-secret" ## TODO: add a real secret key
        }
        # IMPORTANT
        # Periodically fetches and broadcast sensor data to WebSocket clients
        self.periodic_fetch = PeriodicCallback(
            self.fetch_and_broadcast_data, 5000)  # 5000ms = 5 seconds !!!!!
        self.periodic_fetch.start()

        TornadoApplication.__init__(
            self, self.tornado_handlers, **self.tornado_settings)

    def fetch_sensor_data(self) -> list:
        """Fetches the latest sensor data from the database, along with outlier information"""
        session = SessionLocal()
        try:
            # Subquery to fetch the latest sensor data for each team
            latest_timestamp_subquery = (
                session.query(
                    SensorData.team_id,
                    func.max(SensorData.timestamp).label("latest_timestamp")
                )
                .group_by(SensorData.team_id)
                .subquery()
            )

            # Main query to fetch sensor data that corresponds to the latest timestamp for each team
            query = (
                session.query(SensorData)
                .join(latest_timestamp_subquery, (SensorData.team_id == latest_timestamp_subquery.c.team_id) & (SensorData.timestamp == latest_timestamp_subquery.c.latest_timestamp))
            )

            # Fetch the sensor data
            data = query.all()

            # Fetch outlier data for each sensor data record
            # Creating a list of sensor data IDs to fetch the outliers
            sensor_data_ids = [d.id for d in data]

            # Subquery to get the latest outlier for each sensor data record
            sdo = aliased(SensorDataOutliers)
            outlier_subquery = (
                session.query(func.max(sdo.id))
                .join(SensorData, sdo.sensor_data_id == SensorData.id)
                .filter(SensorData.id.in_(sensor_data_ids))
                .group_by(sdo.sensor_data_id)
                .label("max_id")
            )

            # Query to fetch the latest outliers for the relevant sensor data
            outlier_query = (
                session.query(sdo)
                .join(SensorData, sdo.sensor_data_id == SensorData.id)
                .filter(sdo.id == outlier_subquery)
            )

            # Fetch outliers
            outliers_data = outlier_query.all()

            # Create a dictionary to map sensor data IDs to their outlier info
            outlier_dict = {}
            for outlier in outliers_data:
                outlier_dict[outlier.sensor_data_id] = {
                    "is_temperature_out_of_range": outlier.is_temperature_out_of_range,
                    "is_humidity_out_of_range": outlier.is_humidity_out_of_range,
                    "is_illumination_out_of_range": outlier.is_illumination_out_of_range
                }

            # Convert the sensor data to a list of dictionaries with outlier information
            sensor_data_list = [
                {
                    "id": d.id,
                    "team_id": d.team_id,
                    # Assuming team_dict is available elsewhere
                    "team_name": team_dict[d.team_id],
                    "timestamp": convert_to_local_time(d.timestamp.isoformat()).isoformat(),
                    "temperature": d.temperature,
                    "humidity": d.humidity,
                    "illumination": d.illumination,
                    # Add outlier data if available
                    "outliers": outlier_dict.get(d.id, {})
                }
                for d in data
            ]

            total_data_count = session.query(
                func.count(SensorData.id)).scalar()
            now = datetime.now()
            time_interval = now - timedelta(days=1)
            yellow_id = next(
                (key for key, value in team_dict.items() if value == 'yellow'), None)
            # Fetch all data, ordered by team_id and timestamp
            query = (
                session.query(SensorData)
                # Adjust the time range here
                .filter(SensorData.timestamp >= time_interval)
                # Order by team_id and timestamp
                .filter(SensorData.team_id == yellow_id)
                .order_by(SensorData.team_id, SensorData.timestamp)
            )

            # Get all the data for all teams
            all_data = query.all()
            results = [
                {
                    # "team_id": data.team_id,
                    "temperature": data.temperature,
                    "humidity": data.humidity,
                    "illumination": data.illumination,
                    "timestamp": data.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")
                }
                for data in all_data
            ]
            temperatures = [data["temperature"]
                            for data in results if data["temperature"] is not None]
            humidities = [data["humidity"]
                          for data in results if data["humidity"] is not None]
            illuminations = [data["illumination"]
                             for data in results if data["illumination"] is not None]

            # Calculate averages
            average_temperature = np.mean(
                temperatures) if temperatures else None
            average_humidity = np.mean(humidities) if humidities else None
            average_illumination = np.mean(
                illuminations) if illuminations else None
            latest_yellow_timestamp = None
            for sensor_data in sensor_data_list:
                if sensor_data["team_id"] == yellow_id:
                    latest_yellow_timestamp = sensor_data["timestamp"]
        # Prepare the final result dictionary
            result = {
                "sensor_data": sensor_data_list,
                "total_data": total_data_count,
                "average_temperature": average_temperature,
                "average_humidity": average_humidity,
                "average_illumination": average_illumination,
                "latest_yellow_timestamp": latest_yellow_timestamp
            }

            return result

        finally:
            session.close()

    def fetch_and_broadcast_data(self) -> None:
        """Fetches all sensor data and broadcasts to all connected WebSocket clients."""
        sensor_data = self.fetch_sensor_data()
        message = sensor_data
        self.send_ws_message(message)

    def send_ws_message(self, message) -> None:
        """Sends the message to all clients."""
        for client in self.ws_clients:
            iol.spawn_callback(client.write_message, dumps_json(message))


if __name__ == '__main__':
    """Starts the backend application."""
    PORT = 8881
    app = WebWSApp()
    print('Webserver: Initialized. Listening on', PORT)
    team_dict = extract_teams_dict()
    print(team_dict)
    app.listen(PORT)
    iol = IOLoop.current()
    iol.start()
