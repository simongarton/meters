# Hardware options

## Onboard LED

https://projects.raspberrypi.org/en/projects/getting-started-with-the-pico/5

```
from machine import Pin, Timer
led = Pin(25, Pin.OUT)
timer = Timer()

def blink(timer):
    led.toggle()

timer.init(freq=2.5, mode=Timer.PERIODIC, callback=blink)
```

## Breadboards

https://projects.raspberrypi.org/en/projects/getting-started-with-the-pico/6

https://projects.raspberrypi.org/en/projects/getting-started-with-the-pico/7

## Other LEDs

https://projects.raspberrypi.org/en/projects/introduction-to-the-pico/7