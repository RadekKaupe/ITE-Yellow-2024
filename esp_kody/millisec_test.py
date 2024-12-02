from machine import Pin, RTC
import network
import time
import ntptime


sta_if = network.WLAN(network.STA_IF)

if not sta_if.isconnected():
    print('connecting to network...')
    sta_if.active(True)
    sta_if.connect('zcu-hub-ui', 'IoT4ZCU-ui')
    print("connencting to ui-hub")
    while not sta_if.isconnected():
        pass
print('network config:', sta_if.ifconfig())

ntptime.host = "clock1.zcu.cz"
rtc = RTC()
def syncTime():
    try:
        ntptime.settime()   # make sure to have internet connection
    except:
        print("Error syncing time")

# RTC.datetime() gives (year, month, day, weekday, hours, minutes, seconds, subseconds)
def newTimeStamp(tmp):
    return (    "{0}-{1:02}-{2:02}T{3:02}:{4:02}:{5:02}.{6:06}".format(tmp[0], tmp[1], tmp[2], tmp[4], tmp[5], tmp[6], tmp[7]*1000)  ) # (year, month, day, hour, min, sec)



period = 60*1000    # m/s
previous = time.ticks_ms()
now = previous + 1

while(True):
    tmp = rtc.datetime()
    print(newTimeStamp(tmp))
    
    now = time.ticks_ms()
    if(time.ticks_diff(now, previous) >= period): 
        syncTime()
        print("TIME SYNCED --------------------------------------------------------------------------------------")
        previous = now