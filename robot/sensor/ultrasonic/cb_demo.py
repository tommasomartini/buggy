import logging
import threading
import time

import RPi.GPIO as GPIO

TRIG_PIN = 17
ECHO5 = 27
ECHO4 = 18

# From documentation:
#   https://www.robotshop.com/media/files/pdf/hc-sr05-ultrasonic-range-finder-datasheet.pdf
_PULSE_DURATION_s = 10e-6       # 10 microseconds
# It is recommended to trigger at most every 60 ms.
_MEASURE_INTERVAL_s = 60e-3

# Constants.
_SPEED_OF_SOUND_mps = 343.26    # m/s
_INIT_SETUP_TIME_s = 0.2

# Speed-up constants: values that we precompute to save operations at runtime.

# The formula to convert the pulse duration to distance in centimeters is:
#   distance_cm = pulse_duration_s * speed_sound_mps * 100 / 2
# where the x100 is to convert meters in centimeters. The pulse duration equals
# the time from emission to reception, that is the time the sound travelled
# to the target and back. We divide by 2 to consider the distance covered
# in a one-way trip.
_PULSE_TO_DISTANCE_MULTIPLIER_cmps = _SPEED_OF_SOUND_mps * 100 / 2

# We experienced some freezing when using the nominal interval. We allow for
# some slack time.
_EFFECTIVE_MEASURE_INTERVAL_s = 1.2 * _MEASURE_INTERVAL_s


GPIO.setmode(GPIO.BCM)

GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO4, GPIO.IN)
GPIO.setup(ECHO5, GPIO.IN)

def _trigger():
    """Trigger the pulse."""
    GPIO.output(TRIG_PIN, True)
    time.sleep(_PULSE_DURATION_s)
    GPIO.output(TRIG_PIN, False)


listen = False
time_on_4 = -1
time_on_5 = -1
is_on_5 = False

distance5 = -1
distance4 = -1

def callback_5on(channel):
    global time_on_5
    global is_on_5
    global distance5
    if listen:
        is_on_5 = not is_on_5
        if is_on_5:
            # rising
            time_on_5 = time.time()
        else:
            # falling
            distance5 = (time.time() - time_on_5) * _PULSE_TO_DISTANCE_MULTIPLIER_cmps


GPIO.add_event_detect(ECHO5, GPIO.BOTH, callback=callback_5on)


def _main():
    global listen

    
    GPIO.output(TRIG_PIN, False)

    try:
        while True:
            _trigger()
            listen = True
            
            GPIO.wait_for_edge(ECHO4, GPIO.RISING, timeout=1000)
            time_on_4 = time.time()
            GPIO.wait_for_edge(ECHO4, GPIO.FALLING, timeout=1000)
            distance4 = (time.time() - time_on_4) * _PULSE_TO_DISTANCE_MULTIPLIER_cmps
           

            time.sleep(_EFFECTIVE_MEASURE_INTERVAL_s)
            listen = False
            print('[4] {:6.2f}'.format(distance4))
            print('[5] {:6.2f}'.format(distance5))

            

    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()

    print('Bye!')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _logger = logging.getLogger(__name__)
    _main()
