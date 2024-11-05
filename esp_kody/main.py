from machine import Pin
import network
import time
import umqtt

from light_sensor import BH1750
import dht
from temp_sensor import tempSensorDS

ledIn = Pin(2, Pin.OUT)
tempSens = tempSensorDS(pin_nb=5)
humiSens = dht.DHT11(machine.Pin(4))
sda = machine.Pin(0)
scl = machine.Pin(2)
i2c = machine.I2C(scl,sda) # komunikace s light senzorem
lightSens = BH1750(i2c)

sta_if = network.WLAN(network.STA_IF)

BROKER_IP = '147.228.124.47'
BROKER_PORT = 1883
BROKER_UNAME = 'student'
BROKER_PASSWD = 'pivotecepomqtt'
TOPIC = 'ite/yellow'
SLEEP_TIME = 2

if not sta_if.isconnected():
    print('connecting to network...')
    sta_if.active(True)
    sta_if.connect('zcu-hub-ui', 'IoT4ZCU-ui')
    print("connencting to ui-hub")
    while not sta_if.isconnected():
        pass
print('network config:', sta_if.ifconfig())

MQclient = umqtt.MQTTClient("yellow_esp", BROKER_IP, BROKER_PORT, BROKER_UNAME, BROKER_PASSWD)
MQclient.connect()

temp = "Err"     # if these get sent, then we have a problem
tempH = "Err"  
humi = "Err" 
light = "Err"

while(True):
    
    temp = tempSens.measure_temp()
    light = lightSens.luminance(BH1750.ONCE_HIRES_1)
    try:
        humiSens.measure()
        tempH = humiSens.temperature()
        humi = humiSens.humidity()
    except OSError as e:
        tempH = "hErr"     # if these get sent, then we have a problem
        humi = "hErr"
        
    payload = {'team_name': 'yellow', 'timestamp': '2020-03-24T15:26:05.336974', 'temperature': 25.72, 'humidity': 64.5, 'illumination': 1043}
    

    
    
# format: {'team_name': 'white', 'timestamp': '2020-03-24T15:26:05.336974', 'temperature': 25.72, 'humidity': 64.5, 'illumination': 1043}