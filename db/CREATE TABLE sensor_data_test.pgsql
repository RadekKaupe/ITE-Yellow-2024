CREATE TABLE sensor_data_test (
    id SERIAL PRIMARY KEY, -- Auto-incrementing primary key
    team_id INTEGER NOT NULL, -- Foreign key for the team
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Default UTC timestamp
    temperature FLOAT NOT NULL, -- Required temperature value
    humidity FLOAT, -- Optional humidity value
    illumination FLOAT, -- Optional illumination value
    my_timestamp TIMESTAMP, -- Local timestamp
    utc_timestamp TIMESTAMP, -- Explicit UTC timestamp
    CONSTRAINT fk_team FOREIGN KEY (team_id) REFERENCES teams(id) -- Foreign key constraint
);