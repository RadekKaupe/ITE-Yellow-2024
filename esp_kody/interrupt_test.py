from machine import Pin, Timer
from time import sleep

# LED pin
led = Pin(5, Pin.OUT)

# Callback function for the timer
def toggle_led(timer):
    led.value(not led.value())  # Toggle the LED state (ON/OFF)

# Create a periodic timer
blink_timer = Timer(1)
blink_timer.init(mode=Timer.PERIODIC, period=500, callback=toggle_led)  # Timer repeats every half second


    # Main loop (optional)
while True:
    print('Main Loop is running')
    sleep(2)