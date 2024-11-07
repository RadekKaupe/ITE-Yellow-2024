from machine import Pin, Timer
import network
import time
import ntptime

ledIn = Pin(2, Pin.OUT)

sta_if = network.WLAN(network.STA_IF)

if not sta_if.isconnected():
    print('connecting to network...')
    sta_if.active(True)
    sta_if.connect('zcu-hub-ui', 'IoT4ZCU-ui')
    print("connencting to ui-hub")
    while not sta_if.isconnected():
        pass
print('network config:', sta_if.ifconfig())

#if needed, overwrite default time server   2020-03-24T15:26:05.336974
#ntptime.host = "1.europe.pool.ntp.org"
ntptime.host = "clock1.zcu.cz"

def timeFormat():
    tmp = time.localtime()  # (year, month, day, hour, min, sec)
    ms = time.time() - int(time.time())
    return "{0}-{1}-{2}T{3}:{4}:{5:.6f}".format(tmp[0], tmp[1], tmp[2], tmp[3], tmp[4], ms)

while(True):
    
    try:
        print("Local time before synchronization：%s" %str(time.localtime()))
        #make sure to have internet connection
        ntptime.settime()
        print("Local time after synchronization：%s" %str(time.localtime()))
    except:
        print("Error syncing time")
    
    print(timeFormat())
    time.sleep(10)