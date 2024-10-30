from machine import Pin
import network
import time

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

while(True):
    ledIn.on()
    time.sleep_ms(500)
    ledIn.off()
    time.sleep_ms(500)
    
    
# test