import os
import json
import tornado.ioloop
import tornado.web
from tornado import gen
import paho.mqtt.client as mqtt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import sys
from dotenv import load_dotenv

# Get the absolute path of the directory containing db.py
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
print(connection_string)
engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}")

SessionLocal = sessionmaker(bind=engine)
#### LOCALHOST
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")  # Broker address
print("Broker:"+ str(MQTT_BROKER))
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))  
print("Port: "+ str(MQTT_PORT)) # Broker port
MQTT_TOPIC = "sensor/data"                            # Topic to subscribe to
print("topic: "+ MQTT_TOPIC + "\n")
########

#### GOLEM ####
# BROKER_IP = os.getenv("BROKER_IP")
# BROKER_PORT = int(os.getenv("BROKER_PORT"))
# BROKER_UNAME = os.getenv("BROKER_UNAME")
# BROKER_PASSWD = os.getenv("BROKER_PASSWD")
# TOPIC = os.getenv("TOPIC")

# print(f"BROKER_IP = {BROKER_IP}")
# print(f"BROKER_PORT = {BROKER_PORT}")
# print(f"BROKER_UNAME = {BROKER_UNAME}")
# print(f"BROKER_PASSWD = {BROKER_PASSWD}")
# print(f"TOPIC = {TOPIC}")
# #########


#Tornado
class DataHandler(tornado.web.RequestHandler):
    def get(self):
        # Retrieve all sensor data from the database
        session = SessionLocal()
        data = session.query(SensorData).all()
        session.close()
        result = [
            {
                "id": d.id,
                "temperature": d.temperature,
                "humidity": d.humidity,
                "illumination": d.illumination,
                "timestamp": d.timestamp.isoformat(),
            }
            for d in data
        ]
        self.write(json.dumps(result))

    def post(self):
        # Update or adjust sensor data based on request (example for single data point adjustment)
        try:
            payload = json.loads(self.request.body)
            session = SessionLocal()

            # Adjust data based on ID and new values
            data_entry = session.query(SensorData).filter(SensorData.id == payload['id']).first()
            if data_entry:
                data_entry.temperature = payload.get("temperature", data_entry.temperature)
                data_entry.humidity = payload.get("humidity", data_entry.humidity)
                data_entry.illumination = payload.get("illumination", data_entry.illumination)
                session.commit()
                self.write({"status": "success", "message": "Data updated"})
            else:
                self.set_status(404)
                self.write({"status": "error", "message": "Data not found"})

            session.close()

        except Exception as e:
            self.set_status(500)
            self.write({"status": "error", "message": str(e)})

# MQTT 
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        team_name = payload.get("team_name")
        temperature = payload.get("temperature")
        humidity = payload.get("humidity")
        illumination = payload.get("illumination")
        team_id = team_ids[team_name]
        print(team_name)
        print(team_id)
        # Insert data into the database
        session = SessionLocal()
        new_data = SensorData(
            team_id=team_id,
            temperature=temperature,
            humidity=humidity,
            illumination=illumination,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        session.add(new_data)
        session.commit()
        session.close()

        print(f"Data saved: {new_data}")

    except Exception as e:
        print(f"Error saving data: {e}")

# Setup Tornado Application
def make_app():
    return tornado.web.Application([
        (r"/data", DataHandler),  # Endpoint to get or adjust data
    ])

def extract_team_ids(teams):
    teams_ids = dict()
    for team in teams:
        teams_ids[str(team.name)] = team.id
    # print(teams_ids)
    return teams_ids

if __name__ == "__main__":
    # Start Tornado server
    app = make_app()
    app.listen(8881)
    session = SessionLocal()

    teams = session.query(Teams).all()
    team_ids = extract_team_ids(teams) 
    # print(team_ids)
    session.close()
    
    print("Server started at http://localhost:8881")
    print("\n")
    # Setup MQTT client and start listening
    mqtt_client = mqtt.Client()
    mqtt_client.on_message =  on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT) #LOCALHOST
    
    
    #### GOLEM
    # mqtt_client.username_pw_set(BROKER_UNAME, password=BROKER_PASSWD)
    # mqtt_client.connect(BROKER_IP, BROKER_PORT, 60)

    mqtt_client.subscribe(MQTT_TOPIC)
    mqtt_client.loop_start()

    tornado.ioloop.IOLoop.current().start()
