"""Line tracking sensor produced by RobotDyn.

Documentation:
    https://robotdyn.com/line-tracking-sensor.html

Warning!
Although documentation reports:
  "If Line Tracking Sensor detects black color, the signal line (DO)
   of the sensor is HIGH, at the same time the LED (blue) on the sensor
   lights up. If Line Tracking Sensor detect white color, the signal
   line (DO) goes LOW."
what we observe is the following:
* sensor on black surface -> all IR light absorbed
                             no light to receiver
                             DO is HIGH
                             LED is OFF
* sensor on white surface -> all IR light reflected
                             all the light to receiver
                             DO is LOW
                             LED is ON

We deduce that the component is pull-up, because when no signal is received the
signal goes to high state.
"""

IS_PULL_UP = True
