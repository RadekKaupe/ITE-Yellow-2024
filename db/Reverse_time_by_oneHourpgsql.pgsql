-- SELECT timestamp, 
--        timestamp - INTERVAL '1 hour' AS corrected_time
-- FROM sensor_data;

UPDATE sensor_data
SET timestamp = timestamp - INTERVAL '1 hour';