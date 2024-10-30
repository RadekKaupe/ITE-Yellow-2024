from machine import Pin
import network
import time

ledIn = Pin(2, Pin.OUT)

sta_if = network.WLAN(network.STA_IF)
ap_if = network.WLAN(network.AP_IF)

print(sta_if.active())
print(ap_if.active())

print(ap_if.ifconfig())     # novejsi verze toho prikazu

while(True):
    ledIn.on()
    time.sleep_ms(500)
    ledIn.off()
    time.sleep_ms(500)