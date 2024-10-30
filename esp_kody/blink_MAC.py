from machine import Pin

import time
import ubinascii
import network

led = Pin(5, Pin.OUT)
ledIn = Pin(2, Pin.OUT)

wlan_sta = network.WLAN(network.STA_IF)
wlan_sta.active(True)
wlan_mac = wlan_sta.config('mac')
print(ubinascii.hexlify(wlan_mac).decode())

while(True):

    led.on()
    ledIn.on()

    time.sleep_ms(500)

    led.off()
    ledIn.off()

    time.sleep_ms(500)