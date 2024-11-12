-- Insert records for Team 1
INSERT INTO sensor_data (team_id, timestamp, temperature, humidity, illumination)
VALUES (1, '2024-11-12 08:00:00', 22.5, 60.0, 300.0);

-- Insert records for Team 2 (without humidity)
INSERT INTO sensor_data (team_id, timestamp, temperature, humidity, illumination)
VALUES (2, '2024-11-12 09:00:00', 21.8, NULL, 310.0);

-- Insert records for Team 3 (without illumination)
INSERT INTO sensor_data (team_id, timestamp, temperature, humidity, illumination)
VALUES (3, '2024-11-12 10:30:00', 23.1, 58.0, NULL);

-- Insert records for Team 4 (without humidity and illumination)
INSERT INTO sensor_data (team_id, timestamp, temperature, humidity, illumination)
VALUES (4, '2024-11-12 11:45:00', 22.0, NULL, 0);

-- Insert records for Team 5 (with all values present)
INSERT INTO sensor_data (team_id, timestamp, temperature, humidity, illumination)
VALUES (5, '2024-11-12 13:15:00', 20.7, 55.0, 280.0);

-- Insert records for Team 6 (without humidity)
INSERT INTO sensor_data (team_id, timestamp, temperature, humidity, illumination)
VALUES (6, '2024-11-12 14:30:00', 21.3, NULL, 295.0);
