WITH time_series AS (
    SELECT generate_series(
        -- now() - interval '24 hours', -- starting point (24 hours ago)
        -- now(), -- ending point (current time)
        -- interval '20 minutes' -- interval of 20 minutes for 3 entries per hour
        now(), -- starting point (current time)
        now() - interval '24 hours', -- ending point (24 hours ago)
        -interval '20 minutes' -- negative interval for descending order
    ) AS timestamp
)
INSERT INTO sensor_data (team_id, timestamp, temperature, humidity, illumination)
SELECT
    t.id AS team_id, -- each team_id from the teams table
    ts.timestamp,
    -- Generate random values for temperature, humidity, and illumination
    round((random() * 30 + 10)::numeric, 2) AS temperature, -- Random temperature between 10 and 40°C
    CASE WHEN random() < 0.3 THEN NULL ELSE round((random() * 100)::numeric, 2) END AS humidity, -- 30% chance of NULL
    CASE WHEN random() < 0.2 THEN NULL ELSE round((random() * 1000)::numeric, 2) END AS illumination -- 20% chance of NULL
FROM time_series ts
CROSS JOIN teams t; -- Cross join to generate an entry for each team and each timestamp
