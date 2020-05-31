"""Micro Servo 9g SG90.

Documentation:
    http://www.ee.ic.ac.uk/pcheung/teaching/DE1_EE/stores/sg90_datasheet.pdf
"""

MAX_ANGLE_deg = 90                      # operating range is [-90, 90] degrees
MIN_PULSE_WIDTH_s = 5e-4                # 0.5 ms, duty cycle 2.5%
MAX_PULSE_WIDTH_s = 24e-4               # 2.4 ms, duty cycle 12%
FRAME_WIDTH_s = 20e-3                   # 20 ms, 50 Hz
MAX_OPERATING_SPEED_degps = 60. / 0.1   # 600 deg/s (sometimes 400 deg/s)
