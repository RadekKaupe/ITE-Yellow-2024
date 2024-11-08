from machine import Pin, Timer, RTC
import network
import time
import ntptime

ledIn = Pin(2, Pin.OUT)

sta_if = network.WLAN(network.STA_IF)

rtc = RTC()

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
    t = time.time()
    print("secs: " + str(t))
    ms = t - int(t) + tmp[5]
    return "{0}-{1:02}-{2:02}T{3:02}:{4:02}:{5:02.6f}".format(tmp[0], tmp[1], tmp[2], tmp[3], tmp[4], ms)

def syncTime():
    try:
        ntptime.settime()   #make sure to have internet connection
    except:
        print("Error syncing time")
    t = time.time() + 3600
    (year, month, mday, hour, minute, second, weekday, yearday) = time.localtime(t)
    rtc.datetime((year, month, mday, 0, hour, minute, second, 0))

while(True):
    
    print("==============================")
    print("Local time before synchronization：%s" %str(time.localtime()))
    syncTime()
    print("Local time after synchronization：%s" %str(time.localtime()))
    
    print(timeFormat())
    time.sleep(10)