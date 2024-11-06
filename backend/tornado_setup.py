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

# Get the absolute path of the directory containing db.py
db_foler_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db'))

# Add db_foler_path to sys.path
sys.path.insert(0, db_foler_path)
from db import SensorData, SessionLocal  

engine = create_engine(f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}")
SessionLocal = sessionmaker(bind=engine)

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")  # Broker address
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))        # Broker port
MQTT_TOPIC = "sensor/data"                            # Topic to subscribe to

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
        temperature = payload.get("temperature")
        humidity = payload.get("humidity")
        illumination = payload.get("illumination")

        # Insert data into the database
        session = SessionLocal()
        new_data = SensorData(
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

if __name__ == "__main__":
    # Start Tornado server
    app = make_app()
    app.listen(8881)
    print("Server started at http://localhost:8881")

    # Setup MQTT client and start listening
    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.subscribe(MQTT_TOPIC)
    mqtt_client.loop_start()

    tornado.ioloop.IOLoop.current().start()
