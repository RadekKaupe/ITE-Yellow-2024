# from machine import Timer
from machine import Pin, Timer
import json
import network
import time
import ntptime
from machine import I2C
import umqtt
import ntptime
import math

from light_sensor import BH1750
import dht
from temp_sensor import tempSensorDS



ledIn = Pin(2, Pin.OUT)
led = Pin(16, Pin.OUT)
led.on()

tempOnline = True
try: tempSens = tempSensorDS(pin_nb=5)
except: tempOnline = False
humiSens = dht.DHT11(Pin(4))
sda = Pin(0)
scl = Pin(14)
i2c = I2C(scl, sda, freq = 200000) # komunikace s light senzorem
lightSens = BH1750(i2c)

sta_if = network.WLAN(network.STA_IF)
sta_if.disconnect()

BROKER_IP = '147.228.124.47'
BROKER_PORT = 1883
BROKER_UNAME = 'student'
BROKER_PASSWD = 'pivotecepomqtt'
TOPIC = 'ite/yellow'
QOS = 1
TIMEOUT = 0.5   # sec
RECON_PERIOD = 500 # ms

# SLEEP_TIME = 2
MQclient = umqtt.MQTTClient("yellow_esp", BROKER_IP, BROKER_PORT, BROKER_UNAME, BROKER_PASSWD)  

global temp;        temp = 999     # if these get sent, then we have a problem
global tempH;       tempH = 999
global humi;        humi = 999 
global light;       light = 999
global payload

def newTimeStamp(secs):
    tmp = time.localtime(secs) 
    return (    "{0}-{1:02}-{2:02}T{3:02}:{4:02}:{5:09.6f}".format(tmp[0], tmp[1], tmp[2], tmp[3], tmp[4], tmp[5])  ) # (year, month, day, hour, min, sec)

ntptime.host = "clock1.zcu.cz"
#rtc = RTC()
def syncTime():
    try:
        ntptime.settime()   # make sure to have internet connection
        #t = time.time() + 3600 # offset because settime gives time - 1 hour
        #(year, month, mday, hour, minute, second, weekday, yearday) = time.localtime(t)
        #rtc.datetime((year, month, mday, 0, hour, minute, second, 0))
    except:
        print("Error syncing time")
    
def measure():
    global temp
    global tempH
    global humi
    global light
    
    if(tempOnline): temp = round(tempSens.measure_temp(), 2)
    light = int(round(lightSens.luminance(BH1750.ONCE_HIRES_1)))
    try:
        humiSens.measure()
        tempH = round(float(humiSens.temperature()), 2)
        if(not tempOnline): temp = tempH
        humi = round(float(humiSens.humidity()), 1)
    except:
        tempH = "hErr"     # if these get sent, then we have a problem
        humi = "hErr"
  
global connBroker;  connBroker = False
def reconnect():
    global connBroker
    global recPrev
    recPrev = time.ticks_ms()
    if not sta_if.isconnected():
        sta_if.active(True)
        try:
            sta_if.connect('zcu-hub-ui', 'IoT4ZCU-ui')
            #time.sleep_ms(500)
        except Exception as e:
            time.sleep_ms(500)
        except:
            print("connecting to network failed")
        print('connecting to network...')
        
    else:    
        print('network config:', sta_if.ifconfig())
        try:
            MQclient.connect()
            connBroker = True
            print("connected to broker")
        except:
            print("connecting to broker failed")

archive = list()
def publish():
    global payload
    global connBroker
    global recPrev
    t = time.time()
    payload = json.dumps({'team_name': 'yellow', 'timestamp': newTimeStamp(t), 'temperature': temp, 'humidity': humi, 'illumination': light})
    print(payload)
    try:
        MQclient.publish(TOPIC, payload, qos=QOS, timeout=TIMEOUT)
    except Exception as e:
        MQclient.publish(TOPIC, payload, QOS, TIMEOUT)
    except:
        connBroker = False
        recPrev = time.ticks_ms()
        if len(archive) == 0:
            archive.append([t, 0, temp, humi, light])   # index [1] is number of measurements same as this one
        else:
            if(archive[-1][2] == temp and archive[-1][3] == humi and archive[-1][4] == light): archive[-1][1] += 1
            else:
                archive.append([t, 0, temp, humi, light])
        
        
def sendArchive():  
    global connBroker
    global payload
    global recPrev
    archive.reverse()   # older logs last now
    for i in range(0, len(archive)):
        log = archive.pop()
        if(log[1] == 0):
            payload = json.dumps({'team_name': 'yellow', 'timestamp': newTimeStamp(log[0]), 'temperature': log[2], 'humidity': log[3], 'illumination': log[4]})
            try:
                MQclient.publish(TOPIC, payload, qos=QOS, timeout=TIMEOUT)
            except Exception as e:
                MQclient.publish(TOPIC, payload, QOS, TIMEOUT)
            except:
                connBroker = False
                recPrev = time.ticks_ms()
                archive.append(log)
                archive.reverse()   # newer logs last now
                break
                
        else:   
            for j in range(0, log[1]): # send log[1] same logs with timestamps offset by j*period
                payload = json.dumps({'team_name': 'yellow', 'timestamp': newTimeStamp(log[0]+j*period), 'temperature': log[2], 'humidity': log[3], 'illumination': log[4]})
                try:
                    MQclient.publish(TOPIC, payload, qos=QOS, timeout=TIMEOUT)
                except Exception as e:
                    MQclient.publish(TOPIC, payload, QOS, TIMEOUT)
                except:
                    connBroker = False
                    recPrev = time.ticks_ms()
                    log[0] += j*period
                    log[1] -= j
                    archive.append(log)
                    archive.reverse()   # newer logs last now
                    break
        if not connBroker: break
    
#timer1 = Timer(1)
#minPassed = False
#def setFlagMeas(timer):  minPassed = True
#timer1.init(mode=Timer.PERIODIC, period=1000*1, callback=setFlagMeas) 

period = 60*1000
previous = time.ticks_ms()
now = previous + 1

recPrev = time.ticks_ms()
while(True):
    
    now = time.ticks_ms()
    led.value(not connBroker)
    if(not connBroker and time.ticks_diff(now, recPrev) >= RECON_PERIOD): reconnect()
    
    if(time.ticks_diff(now, previous) >= period): 
        ledIn.value(not ledIn.value())
        syncTime()
        measure()
        if(connBroker and len(archive) > 0): sendArchive() 
        publish()
        previous = now
    

    
    

    

    
    
# format: {'team_name': 'white', 'timestamp': '2020-03-24T15:26:05.336974', 'temperature': 25.72, 'humidity': 64.5, 'illumination': 1043}