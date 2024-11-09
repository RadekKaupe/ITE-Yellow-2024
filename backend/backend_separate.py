import os
import json
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import tornado.ioloop
import tornado.web
from tornado import gen

db_foler_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db'))

# Add db_foler_path to sys.path
sys.path.insert(0, db_foler_path)
from db import SensorData, Teams


# Load environment variables
load_dotenv()
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST", "localhost")
db_name = os.getenv("DB_NAME")

# Database setup
connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}"
engine = create_engine(connection_string)
SessionLocal = sessionmaker(bind=engine)

# Tornado request handler
class DataHandler(tornado.web.RequestHandler):
    def get(self):
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
        try:
            payload = json.loads(self.request.body)
            session = SessionLocal()

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

# Tornado app setup
def make_app():
    return tornado.web.Application([
        (r"/data", DataHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8881)
    print("Server started at http://localhost:8881")
    tornado.ioloop.IOLoop.current().start()
