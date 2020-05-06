from time import sleep

from gpiozero import Servo

# Parameters from the datsheet:
#   https://datasheetspdf.com/pdf-file/791970/TowerPro/SG90/1
MIN_PULSE_WIDTH_s = 5e-4            # 0.5 ms, duty cycle 2.5%
MAX_PULSE_WIDTH_s = 24e-4           # 2.4 ms, duty cycle 12%
FRAME_WIDTH_s = 20e-3               # 20 ms, 50 Hz
OPERATING_SPEED_degps = 60. / 0.1   # 60 deg/s
MAX_ANGLE_deg = 90                  # operating range is [-90, 90]

def main():
    servo = Servo(pin=17,
                  initial_value=0,
                  min_pulse_width=MIN_PULSE_WIDTH_s,
                  max_pulse_width=MAX_PULSE_WIDTH_s,
                  frame_width=FRAME_WIDTH_s)

    while True:
        in_val = input(
            'Value in degree [-{}, {}], "q" to exit: '.format(MAX_ANGLE_deg,
                                                              MAX_ANGLE_deg))

        if in_val == 'q':
            servo.mid()
            sleep(0.5)
            print('Bye!')
            return

        try:
            in_val = float(in_val)
        except TypeError:
            continue

        # Compute how long the servo will take to get to the requested position.
        # Use a factor 2 to allow for some slack time.
        required_time = 2 * abs(in_val) / OPERATING_SPEED_degps
        servo.value = in_val / MAX_ANGLE_deg
        sleep(required_time)


if __name__ == '__main__':
    main()
