from machine import Pin, Timer, RTC, json
import network
import time
import ntptime
from machine import I2C
import umqtt
import ntptime

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
# SLEEP_TIME = 2

ntptime.host = "clock1.zcu.cz"

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

global temp;        temp = "Err"     # if these get sent, then we have a problem
global tempH;       tempH = "Err"  
global humi;        humi = "Err" 
global light;       light = "Err"
global timestamp;   timestamp = "Err"
global payload;     payload = "Err"

def timeStampUpdate():
    global timestamp
    
    tmp = time.localtime()  # (year, month, day, hour, min, sec)
    #t = time.time()
    #print("secs: " + str(t))
    #ms = t - int(t) + tmp[5]
    timestamp =  "{0}-{1:02}-{2:02}T{3:02}:{4:02}:{5:02.6f}".format(tmp[0], tmp[1], tmp[2], tmp[3], tmp[4], tmp[5])

rtc = RTC()
def syncTime():
    try:
        ntptime.settime()   # make sure to have internet connection
        t = time.time() + 3600 # offset because settime gives time - 1 hour
        (year, month, mday, hour, minute, second, weekday, yearday) = time.localtime(t)
        rtc.datetime((year, month, mday, 0, hour, minute, second, 0))
    except:
        print("Error syncing time")
    


def measure():
    global temp
    global tempH
    global humi
    global light
    
    temp = round(tempSens.measure_temp(), 2)
    light = int(round(lightSens.luminance(BH1750.ONCE_HIRES_1)))
    try:
        humiSens.measure()
        tempH = round(humiSens.temperature(), 2)
        humi = round(humiSens.humidity(), 1)
    except OSError as e:
        tempH = "hErr"     # if these get sent, then we have a problem
        humi = "hErr"

    return()
    
    
def publish():
    global payload
    payload = json.dumps({'team_name': 'yellow', 'timestamp': timestamp, 'temperature': temp, 'humidity': humi, 'illumination': light})
    MQclient.publish(TOPIC, payload, qos=1)
    
#timer1 = Timer(1)
#minPassed = False
#def setFlagMeas(timer):  minPassed = True
#timer1.init(mode=Timer.PERIODIC, period=1000*1, callback=setFlagMeas) 

while(True):
    
    
    syncTime()
    timeStampUpdate()
    measure()
    publish()
    time.sleep(10)
    
    

    

    
    
# format: {'team_name': 'white', 'timestamp': '2020-03-24T15:26:05.336974', 'temperature': 25.72, 'humidity': 64.5, 'illumination': 1043}