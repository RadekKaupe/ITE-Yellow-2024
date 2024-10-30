from machine import Pin

import time
import ubinascii
import network

from sensor_ds18b20 import tempSensorDS

ledIn = Pin(2, Pin.OUT)

sensor = tempSensorDS(pin_nb=5)

while(True):

    print('Temperature: {}'.format(sensor.measure_temp()))
    ledIn.on()

    time.sleep_ms(500)

    ledIn.off()

    time.sleep_ms(500)