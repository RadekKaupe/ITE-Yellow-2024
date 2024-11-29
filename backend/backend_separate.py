
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
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker, Session, aliased
import sys
from datetime import datetime, time, timedelta
import pytz
from datetime import datetime, timezone


db_foler_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'db'))


# Add db_foler_path to sys.path
sys.path.insert(0, db_foler_path)
from db import SensorData, Teams, SensorDataOutliers


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


def convert_to_local_time(utc_timestamp: str):
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
        try:
            # Fetch and process data for the last 24 hours (default behavior)
            averages = self.fetch_data(days=1)
            self.set_header("Content-Type", "application/json")
            if averages is not None:
                self.write(dumps_json(averages))
        except Exception as e:
            self.set_status(500)
            self.write({"error": str(e)})

    def fetch_data(self, days: int = 1):
        # Create a new session
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
        dt = datetime.fromisoformat(timestamp)
        date = dt.date()
        hour = dt.hour
        timestamp_key = datetime.combine(date, time(hour))
        return timestamp_key.isoformat()

    def fill_dict_with_timestamp_keys(self, timestamp_dict: dict, data: dict):
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


class GraphsHandler(RequestHandler):
    def get(self) -> None:
        self.render("static/graphs_one_day.html")


class GraphData30DaysHandler(GraphDataHandler):
    def get(self):
        try:
            # Fetch and process data for the last 30 days
            averages = self.fetch_data(days=30)
            self.set_header("Content-Type", "application/json")
            if averages is not None:
                self.write(dumps_json(averages))
        except Exception as e:
            self.set_status(500)
            self.write({"error": str(e)})

    def calculate_averages(self, data):
        # Debug message to confirm function is being called.
        # print("Function `calculate_averages` called.")

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

        # Print the intermediate aggregation for verification.
        # print("Aggregated Data for Averages Calculation:")
        # for date, team_data in averages.items():
        #     print(f"Date: {date}, Data: {team_data}")

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

                # # Debug each average calculation.
                # print(f"Date: {date}, Team: {team_id}, Temp: {metrics['temp']}, Avg Temp: {avg_temp}")
                # print(f"Date: {date}, Team: {team_id}, Humi: {metrics['humi']}, Avg Humi: {avg_humi}")
                # print(f"Date: {date}, Team: {team_id}, Illu: {metrics['illu']}, Avg Illu: {avg_illu}")

                # Append the team's daily average data to the results for the date.
                daily_averages[date].append({
                    'team_id': team_id,
                    'mean_temp': avg_temp,
                    'mean_humi': avg_humi,
                    'mean_illu': avg_illu
                })

        # Final debug print of daily averages.
        # print("Final Calculated Daily Averages:")
        # for date, data in daily_averages.items():
        #     print(f"Date: {date}, Data: {data}")

        return daily_averages


class Graphs30DaysHandler(RequestHandler):
    def get(self):
        self.render("static/graphs_one_month.html")

class AlertDataHandler(RequestHandler):
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
            # print(latest_outliers)
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
    
    def get_timestamp_by_record_id(self, record_id, session):
    # Query only the timestamp column for the record with the given id
        timestamp = session.query(SensorData.timestamp).filter(SensorData.id == record_id).first()
        # print(timestamp[0].strftime("%Y-%m-%dT%H:%M:%S.%f"))
        # print(timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f"))
        # return timestamp[0]
        return timestamp[0].strftime("%Y-%m-%dT%H:%M:%S.%f")


class LatestDataHandler(RequestHandler):  # zaručuje loadovani dat pri refreshi
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

    def __init__(self):
        self.ws_clients = []
        self.counter = 0

        self.tornado_handlers = [
            (r'/', MainHandler),
            (r"/graph-data/one-day", GraphDataHandler),
            (r"/graph-data/one-month", GraphData30DaysHandler),
            (r"/alert-data", AlertDataHandler),
            (r'/websocket', WSHandler),
            (r'/latest-data', LatestDataHandler),
            (r'/graphs-one-day', GraphsHandler),
            (r'/graphs-one-month', Graphs30DaysHandler),
            (r'/(.*)', StaticFileHandler,
             {'path': join_path(dirname(__file__), 'static')})
        ]
        self.tornado_settings = {
            "debug": True,
            "autoreload": True
        }
        # Periodically fetch and broadcast sensor data to WebSocket clients
        self.periodic_fetch = PeriodicCallback(
            self.fetch_and_broadcast_data, 5000)  # 5000ms = 5 seconds !!!!!
        self.periodic_fetch.start()

        TornadoApplication.__init__(
            self, self.tornado_handlers, **self.tornado_settings)
        ####
        # self.incrementer = PeriodicCallback(self.increment_and_broadcast, 1000)  # Every 1000ms (1 second)
        # self.incrementer.start()
        # Toto fungovalo, od chatbota


    def fetch_sensor_data(self) -> list:
        """Fetches the latest sensor data from the database, along with outlier information"""
        session = SessionLocal()
        try:
            # Subquery to fetch the latest sensor data for each team
            subquery = (
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
                .join(subquery, (SensorData.team_id == subquery.c.team_id) & (SensorData.timestamp == subquery.c.latest_timestamp))
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
                    "team_name": team_dict[d.team_id],  # Assuming team_dict is available elsewhere
                    "timestamp": convert_to_local_time(d.timestamp.isoformat()).isoformat(),
                    "temperature": d.temperature,
                    "humidity": d.humidity,
                    "illumination": d.illumination,
                    "outliers": outlier_dict.get(d.id, {})  # Add outlier data if available
                }
                for d in data
            ]

            return sensor_data_list

        finally:
            session.close()

    # def fetch_sensor_data(self) -> list:
    #     """Fetches the latest sensor data from the database"""
    #     session = SessionLocal()
    #     try:
    #         subquery = (
    #             session.query(
    #                 SensorData.team_id,
    #                 func.max(SensorData.timestamp).label("latest_timestamp")
    #             )
    #             .group_by(SensorData.team_id)
    #             .subquery()
    #         )

    #         query = (
    #             session.query(SensorData)
    #             .join(subquery, (SensorData.team_id == subquery.c.team_id) & (SensorData.timestamp == subquery.c.latest_timestamp))
    #         )

    #         data = query.all()
    #         # Convert query result to a list of dictionaries for JSON serialization
    #         sensor_data_list = [
    #             {
    #                 "id": d.id,
    #                 "team_id": d.team_id,
    #                 "team_name": team_dict[d.team_id],
    #                 "timestamp": convert_to_local_time(d.timestamp.isoformat()).isoformat(),
    #                 "temperature": d.temperature,
    #                 "humidity": d.humidity,
    #                 "illumination": d.illumination 
    #             }
    #             for d in data
    #         ]
    #         # print(sensor_data_list)
    #         return sensor_data_list

    #     finally:
    #         session.close()
            
            
    def fetch_and_broadcast_data(self) -> None:
        """Fetches all sensor data and broadcasts to all connected WebSocket clients."""
        # print("Fetching latest sensor data for broadcast.")
        # Fetch all data; can be modified to fetch specific teams
        sensor_data = self.fetch_sensor_data()
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


if __name__ == '__main__':
    PORT = 8881
    app = WebWSApp()
    print('Webserver: Initialized. Listening on', PORT)
    team_dict = extract_teams_dict()
    print(team_dict)
    app.listen(PORT)
    iol = IOLoop.current()
    iol.start()
