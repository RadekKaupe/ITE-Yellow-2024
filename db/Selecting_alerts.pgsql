SELECT sdo.*
FROM sensor_data_outliers sdo
JOIN sensor_data sd ON sdo.sensor_data_id = sd.id
WHERE sdo.id = (
    SELECT MAX(sdo2.id)
    FROM sensor_data_outliers sdo2
    JOIN sensor_data sd2 ON sdo2.sensor_data_id = sd2.id
    WHERE sd2.team_id = sd.team_id
)