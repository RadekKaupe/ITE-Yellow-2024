import os
import json
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from jsonschema import validate, ValidationError, SchemaError
import paho.mqtt.client as mqtt
import pytz
from datetime import datetime, timezone
import time

db_foler_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db'))

# Add db_foler_path to sys.path
sys.path.insert(0, db_foler_path)
from db import SensorData, Teams, SensorDataTest
aimtec_foler_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'aimtec'))

# Add db_foler_path to sys.path
sys.path.insert(0, aimtec_foler_path)
import aimtec



# Load environment variables
load_dotenv()
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST", "localhost")
db_name = os.getenv("DB_NAME")

connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}"
engine = create_engine(connection_string)
SessionLocal = sessionmaker(bind=engine)

# Define schema
valid_schema = {
    "type": "object",
    "properties": {
        "team_name": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "temperature": {"type": "number"},
        "illumination": {"type": "number"},
        "humidity": {"type": "number"},
        
    },
    "required": ["team_name", "temperature", "timestamp"],
    "additionalProperties": False
}

LOCAL_TIMEZONE = pytz.timezone("Europe/Prague")

#### LOCALHOST
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")  # Broker address
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))  
TOPIC = "sensor/data"                            # Topic to subscribe to
QOS = 2

########

#### GOLEM ####
BROKER_IP = os.getenv("BROKER_IP")
BROKER_PORT = int(os.getenv("BROKER_PORT"))
BROKER_UNAME = os.getenv("BROKER_UNAME")
BROKER_PASSWD = os.getenv("BROKER_PASSWD")
TOPIC = os.getenv("TOPIC")

# #########
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



# Helper functions
def extract_team_ids(teams):
    teams_ids = dict()
    for team in teams:
        teams_ids[str(team.name)] = team.id
    # print(teams_ids)
    return teams_ids
def extract_team_names(teams):
    team_names = set()
    for team in teams:
        team_names.add(team.name)
    return team_names

def check_json(data, schema):
    try:
        validate(data, schema)
    except ValidationError as e:
        print("Validation Error occured.")
        print(data)
        return False
    except SchemaError as e:
        print("Schema error occured")
        return False
    return True

# MQTT message handling
def on_message(client, userdata, msg) -> None:
    try:
        global aimtec_sensors
        payload = json.loads(msg.payload.decode())
        if not check_json(payload, valid_schema):
            print("Invalid payload schema.\n")
            return
        print("Valid Scheme, continuing.")
        print(payload)
        if payload["team_name"] == "yellow":
            send_to_aimtec(payload, aimtec_sensors)
        # save_to_db(payload=payload)
    except Exception as e:
        print(f"Error saving data: {e}")

def send_to_aimtec(payload, aimtec_sensors):
    aimtec_temp_sensor = aimtec_sensors[0]
    aimtec_humi_sensor = aimtec_sensors[1]
    aimtec_illu_sensor = aimtec_sensors[2]
    # print(aimtec_temp_sensor)
    # print(aimtec_humi_sensor)
    # print(aimtec_illu_sensor)
    # print(f"{aimtec.check_if_value_in_range(payload, aimtec_temp_sensor)}\n")
    # print(f"{aimtec.check_if_value_in_range(payload, aimtec_humi_sensor)}\n")
    # print(f"{aimtec.check_if_value_in_range(payload, aimtec_illu_sensor)}\n")
    # print(payload)
    aimtec.post_measurement_all(payload, aimtec_sensors)
    if not aimtec.check_if_value_in_range(payload, aimtec_temp_sensor): ### TOHLE udělej líp
        aimtec.post_alert(payload, aimtec_temp_sensor)
    if not aimtec.check_if_value_in_range(payload, aimtec_humi_sensor):
        aimtec.post_alert(payload, aimtec_humi_sensor)
    if not aimtec.check_if_value_in_range(payload, aimtec_illu_sensor):
        aimtec.post_alert(payload, aimtec_illu_sensor)
    
def save_to_db(payload):
    try:
        
        session = SessionLocal()
        team_ids = extract_team_ids(session.query(Teams).all())
        team_name = payload.get("team_name")
        
        if team_name not in team_ids:
            print("Invalid team name.\n")
            return

        utc_timestamp = payload.get("timestamp")
        
        new_data = SensorData(
            team_id=team_ids[team_name],
            temperature=payload.get("temperature"),
            humidity=payload.get("humidity"),
            illumination=payload.get("illumination"),
            timestamp=utc_timestamp
        )

        session.add(new_data)
        session.commit()
        print(f"Data saved to test db: {new_data}\n")
        local_timestamp = convert_to_local_time(utc_timestamp)
        new_data = SensorDataTest(
            team_id=team_ids[team_name],
            temperature=payload.get("temperature"),
            humidity=payload.get("humidity"),
            illumination=payload.get("illumination"),
            timestamp=local_timestamp,
            utc_timestamp = utc_timestamp,
            my_timestamp = convert_to_local_time(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f"))
        )


        # print(payload)
        session.add(new_data)
        session.commit()
        print(f"Data saved to real db: {new_data} \n")
    except:
        print(f"Error saving data: {e}")    


# Initialize and start MQTT client
def start_local_host_client(): #LOCAL HOST
    print("Broker:"+ str(MQTT_BROKER))
    print("Port: "+ str(MQTT_PORT)) # Broker port
    print("topic: "+ TOPIC + "\n")
    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.subscribe(TOPIC, qos = QOS)
    mqtt_client.loop_forever()
    print("Loop not started")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(TOPIC, qos = QOS)  # Subscribe to the topic upon successful connection
    else:
        print(f"Failed to connect, return code {rc}")

# Callback for when the client disconnects from the broker
def on_disconnect(client, userdata, rc):
    print("Disconnected from MQTT Broker!")
    if rc != 0:
        print("Unexpected disconnection. Attempting to reconnect...")

# Start communication with the MQTT broker
def start_communication_via_broker():
    global aimtec_sensors
    print(f"BROKER_IP = {BROKER_IP}")
    print(f"BROKER_PORT = {BROKER_PORT}")
    print(f"BROKER_UNAME = {BROKER_UNAME}")
    print(f"BROKER_PASSWD = {BROKER_PASSWD}")
    print(f"TOPIC = {TOPIC}")

    mqtt_client = mqtt.Client()

    # Assign callbacks
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message

    # Set username and password
    mqtt_client.username_pw_set(BROKER_UNAME, password=BROKER_PASSWD)

    # Start a background thread for MQTT communication
    mqtt_client.loop_start()

    # Keep trying to connect to the broker
    while True:
        try:
            print("Attempting to connect to MQTT Broker...")
            mqtt_client.connect(BROKER_IP, BROKER_PORT, 60)
            mqtt_client.subscribe(TOPIC, qos = QOS)
            aimtec_sensors = aimtec.get_aimtec_sensor_dicts()
            break  # Exit the loop if connected successfully
        except Exception as e:
            print(f"Connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)

    # Keep the main thread alive
    while True:
        time.sleep(1)
    
if __name__ == "__main__":
    #start_local_host_client()
    start_communication_via_broker()
