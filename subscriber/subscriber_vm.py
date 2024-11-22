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


db_foler_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db'))

# Add db_foler_path to sys.path
sys.path.insert(0, db_foler_path)
from db import SensorData, Teams, SensorDataTest



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

########

#### GOLEM ####
BROKER_IP = os.getenv("BROKER_IP")
BROKER_PORT = int(os.getenv("BROKER_PORT"))
BROKER_UNAME = os.getenv("BROKER_UNAME")
BROKER_PASSWD = os.getenv("BROKER_PASSWD")
TOPIC = os.getenv("TOPIC")

# #########

# #### ZBYTECNA FUNKCE
def check_necessary_keys(msg)->bool:
    required_keys = ["team_name", "temperature"]
    optional_keys = ["humidity", "illumination"]
    try:
        payload = json.loads(msg.payload.decode())
        if all(key in payload for key in required_keys):
            print("All necessary keys are present.")
        else:
            print("Necessary keys are not present. Returning None.")
            return None
         
        for key in optional_keys:
            if key not in payload:
                payload[key] = None  # Set missing optional keys to None

        return payload
    except json.JSONDecodeError as e:
        print(f"Error parsing the JSON: {e}")
        return None
    except Exception as e:
        print(f"An Unknown error occured: {e}")
        return None
    
    ### ### 

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
        payload = json.loads(msg.payload.decode())
        if not check_json(payload, valid_schema):
            print("Invalid payload schema.\n")
            return
        print("Valid Scheme, continuing.")
        session = SessionLocal()
        team_ids = extract_team_ids(session.query(Teams).all())
        team_name = payload.get("team_name")
        
        if team_name not in team_ids:
            print("Invalid team name.\n")
            return

        utc_timestamp = payload.get("timestamp")
        local_timestamp = convert_to_local_time(utc_timestamp)
        new_data = SensorData(
            team_id=team_ids[team_name],
            temperature=payload.get("temperature"),
            humidity=payload.get("humidity"),
            illumination=payload.get("illumination"),
            timestamp=local_timestamp
        )

        session.add(new_data)
        session.commit()
        
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
        print(f"Data saved: {new_data} \n")
    except Exception as e:
        print(f"Error saving data: {e}")

# Initialize and start MQTT client
def start_local_host_client(): #LOCAL HOST
    print("Broker:"+ str(MQTT_BROKER))
    print("Port: "+ str(MQTT_PORT)) # Broker port
    print("topic: "+ TOPIC + "\n")
    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.subscribe(TOPIC)
    mqtt_client.loop_forever()
    print("Loop not started")

def start_communication_via_broker(): # GOLEM
    print(f"BROKER_IP = {BROKER_IP}")
    print(f"BROKER_PORT = {BROKER_PORT}")
    print(f"BROKER_UNAME = {BROKER_UNAME}")
    print(f"BROKER_PASSWD = {BROKER_PASSWD}")
    print(f"TOPIC = {TOPIC}")
    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.username_pw_set(BROKER_UNAME, password=BROKER_PASSWD)
    mqtt_client.connect(BROKER_IP, BROKER_PORT, 60)
    mqtt_client.subscribe(TOPIC)
    mqtt_client.loop_forever()
    
if __name__ == "__main__":
    #start_local_host_client()
    start_communication_via_broker()
