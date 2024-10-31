import machine
from light_sensor import BH1750

# init eps8266 i2c
sda = machine.Pin(0)
scl = machine.Pin(2)

i2c = machine.I2C(scl,sda)

s = BH1750(i2c)

while True:
    s.luminance(BH1750.ONCE_HIRES_1)

