from machine import Pin, Timer
import network
import time
from machine import Timer
from machine import I2C
import umqtt

from light_sensor import BH1750
import dht
from temp_sensor import tempSensorDS



ledIn = Pin(2, Pin.OUT)
tempSens = tempSensorDS(pin_nb=5)
humiSens = dht.DHT11(Pin(4))
sda = Pin(0)
scl = Pin(2)
i2c = I2C(scl,sda) # komunikace s light senzorem
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
payload = {}

def measure(timer):
    temp = round(tempSens.measure_temp(), 2)
    light = round(lightSens.luminance(BH1750.ONCE_HIRES_1))
    try:
        humiSens.measure()
        tempH = round(humiSens.temperature(), 2)
        humi = round(humiSens.humidity(), 1)
    except OSError as e:
        tempH = "hErr"     # if these get sent, then we have a problem
        humi = "hErr"
    
    payload = {'team_name': 'yellow', 'timestamp': '2020-03-24T15:26:05.336974', 'temperature': temp, 'humidity': humi, 'illumination': light}
    MQclient.publish(TOPIC, payload, qos=1)
   
timer = Timer(1)
timer.init(mode=Timer.PERIODIC, period=1000*60, callback=measure) 

while(True):
    
    pass
    
    

    

    
    
# format: {'team_name': 'white', 'timestamp': '2020-03-24T15:26:05.336974', 'temperature': 25.72, 'humidity': 64.5, 'illumination': 1043}