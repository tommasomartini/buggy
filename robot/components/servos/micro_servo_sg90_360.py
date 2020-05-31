"""Micro Servo 9g SG90 360 degrees.
Provides continuous 360 degrees rotation.

See (the closest I found to a datasheet):
    https://www.electrokit.com/en/product/servo-msr-1-3-9-360-2/
"""

MIN_PULSE_WIDTH_s = 5e-4                # 0.9 ms, duty cycle 4.5%
MAX_PULSE_WIDTH_s = 24e-4               # 2.1 ms, duty cycle 10.5%
FRAME_WIDTH_s = 20e-3                   # 20 ms, 50 Hz
MAX_OPERATING_SPEED_degps = 60. / 0.1   # 600 deg/s at 4.8 V
