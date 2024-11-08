import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
from dotenv import load_dotenv
import os

# Define SQLAlchemy Base

Base = declarative_base()

class Teams(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    sensor_data = relationship("SensorData", back_populates="team")

class SensorData(Base):
    __tablename__ = "sensor_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    timestamp = Column(DateTime, default= datetime.datetime.now(datetime.timezone.utc), unique=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    illumination = Column(Float, nullable=False)
    team = relationship("Teams", back_populates="sensor_data")



def create_teams():
    teams = ['blue', 'black', 'green', 'pink', 'red', 'yellow']

    # Start a new session
    with Session(engine) as session:
        # Iterate over the team names and add them to the database
        for team_name in teams:
            team = Teams(name=team_name)  # Replace 'name' with the correct column name if it's different
            session.add(team)
        
        # Commit the transaction to save changes
        session.commit()
        session.close()



#
if __name__ == "__main__":
    
    load_dotenv()
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_name = os.getenv("DB_NAME")
    
    connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}"
    print(connection_string)
    engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}")
    SessionLocal = sessionmaker(bind=engine)
    # Base.metadata.create_all(engine)
    # Base.metadata.drop_all(engine)
    # print("Tables dropped successfully.")
    # create_teams()


