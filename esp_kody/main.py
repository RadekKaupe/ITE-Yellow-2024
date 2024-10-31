from machine import Pin
import network
import time
import umqtt

ledIn = Pin(2, Pin.OUT)

sta_if = network.WLAN(network.STA_IF)

BROKER_IP = '147.228.124.47'
BROKER_PORT = 1883
BROKER_UNAME = 'student'
BROKER_PASSWD = 'pivotecepomqtt'
TOPIC = 'ite/yellow'
SLEEP_TIME = 2

if not sta_if.isconnected():
    print('connecting to network...')
    sta_if.active(True)
    sta_if.connect('zcu-hub-ui', 'IoT4ZCU-ui')
    print("connencting to ui-hub")
    while not sta_if.isconnected():
        pass
print('network config:', sta_if.ifconfig())

MQclient = umqtt.MQTTClient("yellow_esp", BROKER_IP, BROKER_PORT, BROKER_UNAME, BROKER_PASSWD)

while(True):
    ledIn.on()
    time.sleep_ms(500)
    ledIn.off()
    time.sleep_ms(500)
    
