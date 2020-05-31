"""Micro Servo 9g TS90A by TianKongRC.

Documentation:
    https://www.aliexpress.com/item/32972813819.html
"""

MAX_ANGLE_deg = 90                      # operating range is [-90, 90] degrees
MIN_PULSE_WIDTH_s = 5e-4                # 0.5 ms, duty cycle 2.5%
MAX_PULSE_WIDTH_s = 25e-4               # 2.4 ms, duty cycle 12%
FRAME_WIDTH_s = 20e-3                   # 20 ms, 50 Hz
MAX_OPERATING_SPEED_degps = 60. / 0.1   # 600 deg/s (sometimes 400 deg/s)
