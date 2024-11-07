import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime, timezone

MQTT_BROKER = "localhost"  # Adjust if using a different host
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/data"  # Topic that the backend is subscribed to
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT)

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


def publish_fake_data():
    teams = ['blue', 'black', 'green', 'pink', 'red', 'yellow']
    
    while True:
        date = datetime.now(timezone.utc).isoformat()
        # print(date)
        # Create fake data
        data = {
            'team_name': random.choice(teams),
            'timestamp': date,
            'temperature': round(random.uniform(15, 30), 2),  # Fake temperature between 15-30°C
            'humidity': round(random.uniform(30, 70), 2),     # Fake humidity between 30-70%
            'illumination': round(random.uniform(100, 1000), 2)  # Fake illumination in some unit
        }
        
        # Convert data to JSON format
        payload = json.dumps(data)
        
        # Publish the data to the MQTT topic
        client.publish(MQTT_TOPIC, payload)
        print(f"Published data: {payload}")
        
        # Wait for 5 seconds before sending the next message
        time.sleep(5)

if __name__ == "__main__":
    publish_fake_data()
