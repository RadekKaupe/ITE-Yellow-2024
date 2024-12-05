
from machine import Pin, reset, RTC
import json
import network
import time
import ntptime
from machine import I2C
import umqtt
from io import StringIO
import sys


from light_sensor import BH1750
import dht
from temp_sensor import tempSensorDS

errStream = StringIO()

ledIn = Pin(2, Pin.OUT)
led = Pin(16, Pin.OUT)
led.on()

tempOnline = True
try: tempSens = tempSensorDS(pin_nb=5)
except: tempOnline = False; print("temperature unavailable")
try: humiSens = dht.DHT11(Pin(4))
except: print("humidity unavailable")
sda = Pin(0)
scl = Pin(14)
i2c = I2C(scl, sda, freq = 200000) # komunikace s light senzorem
try: lightSens = BH1750(i2c)
except: print("light unavailable")

sta_if = network.WLAN(network.STA_IF)
try: sta_if.disconnect()
except: print("Already disconnected")



BROKER_IP = '147.228.124.47'
BROKER_PORT = 1883
BROKER_UNAME = 'student'
BROKER_PASSWD = 'pivotecepomqtt'
TOPIC = 'ite/yellow'
QOS = 1
TIMEOUT = 0.5   # sec
RECON_PERIOD = 4500 # ms

# SLEEP_TIME = 2
MQclient = umqtt.MQTTClient("yellow_esp", BROKER_IP, BROKER_PORT, BROKER_UNAME, BROKER_PASSWD)  




rtc = RTC()

global temp;        temp = 99     # if these get sent, then we have a problem
global tempH;       tempH = 99
global humi;        humi = 99
global light;       light = 999
global t;           t = 999
global t_tuple;     t_tuple = rtc.datetime()
global payload


ntptime.host = "clock1.zcu.cz"
rtc = RTC()
def syncTime():
    try: ntptime.settime()   # make sure to have internet connection
    except: print("Error syncing time")

print('connecting to network...')
sta_if.active(True)
sta_if.connect('zcu-hub-ui', 'IoT4ZCU-ui')
print("connencting to ui-hub")
while not sta_if.isconnected():
    pass
print('network config:', sta_if.ifconfig())
syncTime()

global connBroker;  connBroker = False
led.value(not connBroker)
while not connBroker:
    try:
        MQclient.connect()
        connBroker = True
        print("connected to broker")
    except:
        print("connecting to broker failed")

# RTC.datetime() gives (year, month, day, weekday, hours, minutes, seconds, subseconds)
def newTimeStamp(tmp):
    print(tmp)
    return (    "{0}-{1:02}-{2:02}T{3:02}:{4:02}:{5:02}.{6:06}".format(tmp[0], tmp[1], tmp[2], tmp[4], tmp[5], tmp[6], tmp[7]*1000)  ) # (year, month, day, hour, min, sec, millisecs)
 
# for sending from archive   
def newTimeStampArchive(secs, millis):
    tmp = time.localtime(secs) 
    return (    "{0}-{1:02}-{2:02}T{3:02}:{4:02}:{5:02}.{6:06}".format(tmp[0], tmp[1], tmp[2], tmp[3], tmp[4], tmp[5], millis*1000)  ) # (year, month, day, hour, min, sec)
    

def measure():
    global temp
    global tempH
    global humi
    global light
    global t
    global t_tuple
    
    t_tuple = rtc.datetime()
    t = time.time()
    
    if(tempOnline): temp = round(tempSens.measure_temp(), 2)
    try: light = int(round(lightSens.luminance(BH1750.ONCE_HIRES_1)))
    except: light = 999
    try:
        humiSens.measure()
        tempH = round(float(humiSens.temperature()), 2)
        if(not tempOnline): temp = tempH
        humi = round(float(humiSens.humidity()), 1)
    except:
        tempH = 99     # if these get sent, then we have a problem
        if(not tempOnline): temp = tempH
        humi = 99
        
    if(time.localtime(t)[5] != t_tuple[6]): t -= 1
  

def reconnect():
    global connBroker
    global recPrev
    recPrev = time.ticks_ms()
    if not sta_if.isconnected():
        sta_if.active(True)
        try:
            sta_if.connect('zcu-hub-ui', 'IoT4ZCU-ui')
            #time.sleep_ms(500)
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
    payload = json.dumps({'team_name': 'yellow', 'timestamp': newTimeStamp(t_tuple), 'temperature': temp, 'humidity': humi, 'illumination': light})
    print(payload)
    try:
        MQclient.publish(TOPIC, payload, qos=QOS, timeout=TIMEOUT)
    except:
        connBroker = False
        recPrev = time.ticks_ms()
        if len(archive) == 0:
            archive.append([t, 0, temp, humi, light, t_tuple[7]])   # index [1] is number of measurements same as this one
        else:
            if(archive[-1][2] == temp and archive[-1][3] == humi and archive[-1][4] == light): archive[-1][1] += 1
            else:
                archive.append([t, 0, temp, humi, light, t_tuple[7]])   # index [5] are milliseconds
        

def archiveAppend():
    if len(archive) == 0:
            archive.append([t, 0, temp, humi, light, t_tuple[7]])   # index [1] is number of measurements same as this one
    else:
        if(archive[-1][2] == temp and archive[-1][3] == humi and archive[-1][4] == light): archive[-1][1] += 1
        else:
            archive.append([t, 0, temp, humi, light, t_tuple[7]])
    print("log archived")

def sendArchive():  
    global connBroker
    global payload
    global recPrev
    archive.reverse()   # older logs last now
    for i in range(0, len(archive)):
        log = archive.pop()
        if(log[1] == 0):
            payload = json.dumps({'team_name': 'yellow', 'timestamp': newTimeStampArchive(log[0], log[5]), 'temperature': log[2], 'humidity': log[3], 'illumination': log[4]})
            try:
                MQclient.publish(TOPIC, payload, qos=QOS, timeout=TIMEOUT)
            except:
                connBroker = False
                recPrev = time.ticks_ms()
                archive.append(log)
                archive.reverse()   # newer logs last now
                break
                
        else:   
            for j in range(0, log[1]+1): # send log[1]+1 same logs with timestamps offset by j*period
                payload = json.dumps({'team_name': 'yellow', 'timestamp': newTimeStampArchive(log[0]+j*(period/1000), log[5]), 'temperature': log[2], 'humidity': log[3], 'illumination': log[4]})
                try:
                    MQclient.publish(TOPIC, payload, qos=QOS, timeout=TIMEOUT)
                except:
                    connBroker = False
                    recPrev = time.ticks_ms()
                    log[0] += j*(period/1000)
                    log[1] -= j
                    archive.append(log)
                    archive.reverse()   # newer logs last now
                    break
        if not connBroker: break
    
#timer1 = Timer(1)
#minPassed = False
#def setFlagMeas(timer):  minPassed = True
#timer1.init(mode=Timer.PERIODIC, period=1000*1, callback=setFlagMeas) 

period = 60*1000    # m/s
previous = time.ticks_ms()
now = previous + 1

recPrev = time.ticks_ms()
try:
    while(True):
        
        now = time.ticks_ms()
        led.value(not connBroker)
        if(not connBroker and time.ticks_diff(now, recPrev) >= RECON_PERIOD): reconnect()
        
        if(time.ticks_diff(now, previous) >= period): 
            ledIn.value(not ledIn.value())
            measure()
            if sta_if.isconnected(): syncTime()
            if(connBroker and len(archive) > 0): sendArchive() 
            if(connBroker): publish()
            else: archiveAppend()
            previous = now
            
except Exception as e:
    
    print("Fatal Error")
    t_tuple = rtc.datetime()
    sys.print_exception(e, errStream)
    msg = errStream.getvalue()
    print(msg)
    tmp = json.dumps({'team_name': 'yellow', 'timestamp': newTimeStamp(t_tuple), 'error': msg})
    
    try: sta_if.disconnect()
    except: print("Already disconnected")
    
    #connBroker2 = False
    while(True):
    
        if not sta_if.isconnected():
            sta_if.active(True)
            try:
                while(not sta_if.isconnected()):
                    sta_if.connect('zcu-hub-ui', 'IoT4ZCU-ui')
                    print('connecting to network...')
                    time.sleep_ms(RECON_PERIOD)
            except:
                print("connecting to network failed")
                #connBroker2 = False
                continue
            
        #if(not connBroker2):   
        try:
            MQclient.connect()
            print("connected to broker")
            #connBroker2 = True
        except:
            print("connecting to broker failed")
            #connBroker2 = False
            continue
            
        try:
            MQclient.publish(TOPIC, tmp, qos=QOS, timeout=TIMEOUT)
            break
        except:
            #connBroker2 = False
            print("error publishing failed")
            continue
        
    reset()
            

    
    

    

    
    
# format: {'team_name': 'white', 'timestamp': '2020-03-24T15:26:05.336974', 'temperature': 25.72, 'humidity': 64.5, 'illumination': 1043}