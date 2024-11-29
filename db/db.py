import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
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
    sensor_data_test = relationship("SensorDataTest", back_populates="team")


class SensorData(Base):
    __tablename__ = "sensor_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    # mam unique, uvidim, jak vyresim prichod vice stejnych zprav
    timestamp = Column(
        DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=True)  # mohou byt NU::
    illumination = Column(Float, nullable=True)  # mohou byt NU::
    team = relationship("Teams", back_populates="sensor_data")
    outliers = relationship("SensorDataOutliers", back_populates="sensor_data")


class SensorDataOutliers(Base):
    __tablename__ = "sensor_data_outliers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_data_id = Column(Integer, ForeignKey(
        "sensor_data.id"), nullable=False)
    is_temperature_out_of_range = Column(
        Boolean, nullable=False, default=False)
    is_humidity_out_of_range = Column(Boolean, nullable=False, default=False)
    is_illumination_out_of_range = Column(
        Boolean, nullable=False, default=False)
    sensor_data = relationship("SensorData", back_populates="outliers")


class SensorDataTest(Base):
    __tablename__ = "sensor_data_test"

    # Auto-incrementing primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key column referencing the teams table
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    # Default UTC timestamp
    timestamp = Column(
        DateTime, default=datetime.datetime.now(datetime.timezone.utc))

    # Required temperature value
    temperature = Column(Float, nullable=False)

    # Optional humidity value
    humidity = Column(Float, nullable=True)

    # Optional illumination value
    illumination = Column(Float, nullable=True)

    # Local timestamp (no default)
    my_timestamp = Column(DateTime, nullable=True)

    # Explicit UTC timestamp (no default)
    utc_timestamp = Column(DateTime, nullable=True)

    # Optional relationship with the Teams model, if needed
    team = relationship("Teams", back_populates="sensor_data_test")


def create_teams() -> None:
    teams = ['blue', 'black', 'green', 'pink', 'red', 'yellow']

    # Start a new session
    with Session(engine) as session:
        # Iterate over the team names and add them to the database
        for team_name in teams:
            # Replace 'name' with the correct column name if it's different
            team = Teams(name=team_name)
            session.add(team)

        # Commit the transaction to save changes
        session.commit()
        session.close()


def choose_action() -> int:
    valid_answers = [0, 1, 2, 9]
    print("Please enter a number based on your decision. ")
    print(f"Press {valid_answers[0]} if you want to create the tables.")
    print(
        f"Press {valid_answers[1]} if you want to create the teams in the TEAMS table.")
    print(
        f"Press {valid_answers[2]} if you want to create the tables and create the teams at once.")
    print(f"Press {valid_answers[3]} if you want to drop all the tables.")
    decision = int(input())
    while decision not in valid_answers:
        print("Input a valid number")
        decision = int(input())
    return decision


def validate_deletion() -> bool:
    phrase = f"Yes, I'm sure"
    print("Are you sure you want to drop the tables?")
    print(f"If you are sure, type: {phrase} ")
    validation = input()
    return validation == phrase


#
if __name__ == "__main__":

    load_dotenv()
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_name = os.getenv("DB_NAME")

    connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}"
    print(connection_string)
    engine = create_engine(
        f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}")
    SessionLocal = sessionmaker(bind=engine)
    action = choose_action()
    if action == 0:
        Base.metadata.create_all(engine)
        print("Tables created successfully.")
    elif action == 1:
        create_teams()
        print("Teams created successfully.")
    elif action == 2:
        Base.metadata.create_all(engine)
        create_teams()
        print("Tables and teams created successfully.")
    elif action == 9:
        if validate_deletion():
            Base.metadata.drop_all(engine)
            print("Tables dropped successfully.")
        else:
            print("Deletion failed, you didn't write the correct phrase.")
