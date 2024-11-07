from machine import Pin
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

#if needed, overwrite default time server
#ntptime.host = "1.europe.pool.ntp.org"
ntptime.host = "clock1.zcu.cz"

while(True):
    
    try:
        print("Local time before synchronization：%s" %str(time.localtime()))
        #make sure to have internet connection
        ntptime.settime()
        print("Local time after synchronization：%s" %str(time.localtime()))
    except:
        print("Error syncing time")
    
    time.sleep(10)