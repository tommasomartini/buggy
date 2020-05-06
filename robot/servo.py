import logging
import threading
import time

from gpiozero import Servo

import common.network as network

SPEED_degps = 60

# Parameters from the datsheet:
#   https://datasheetspdf.com/pdf-file/791970/TowerPro/SG90/1
MAX_ANGLE_deg = 90                      # operating range is [-90, 90]
MIN_PULSE_WIDTH_s = 5e-4                # 0.5 ms, duty cycle 2.5%
MAX_PULSE_WIDTH_s = 24e-4               # 2.4 ms, duty cycle 12%
FRAME_WIDTH_s = 20e-3                   # 20 ms, 50 Hz
MAX_OPERATING_SPEED_degps = 60. / 0.1   # 600 deg/s (sometimes 400 deg/s)

# Movements are performed as tiny subsequent steps with this magnitude.
_STEP_ANGLE_deg = 1

_STRING_ENCODING = 'utf-8'


def _main():
    if SPEED_degps > MAX_OPERATING_SPEED_degps:
        raise ValueError(
            'Set speed ({:.2f} deg/s) exceeds '
            'the maximum operating speed ({:.2f} deg/s)'.format(
                SPEED_degps, MAX_OPERATING_SPEED_degps))

    # The time to wait after each movement is computed from the requested speed
    # and the step size. For a smoother motion, lower the step angle.
    # To increase robustness, we double the nominal waiting time.
    waiting_time_s = 2 * _STEP_ANGLE_deg / SPEED_degps

    servo = Servo(pin=17,
                  initial_value=0,
                  min_pulse_width=MIN_PULSE_WIDTH_s,
                  max_pulse_width=MAX_PULSE_WIDTH_s,
                  frame_width=FRAME_WIDTH_s)

    # Leave the servo the time to initialize.
    time.sleep(0.5)

    _logger.debug('Servo initialized')

    server = network.UDPServer(ip=network.RASPBERRYPI_HOSTNAME,
                               port=network.PORT)

    curr_angle = 0
    direction = 0

    # This function will be called in a dedicated thread to move the servo.
    def _move_servo():
        nonlocal curr_angle
        while True:
            if direction is None:
                break

            elif direction == 0:
                # Do not move.
                pass

            elif direction < 0:
                # Spin left.
                curr_angle -= _STEP_ANGLE_deg
                curr_angle = - MAX_ANGLE_deg \
                    if curr_angle < - MAX_ANGLE_deg else curr_angle

            elif direction > 0:
                # Spin right.
                curr_angle += _STEP_ANGLE_deg
                curr_angle = MAX_ANGLE_deg \
                    if curr_angle > MAX_ANGLE_deg else curr_angle

            # The minus sign is for arbitrary reasons: it depends on how
            # the servo is mounted and whether the motor or the shaft is
            # considered to be spinning.
            servo.value = - curr_angle / MAX_ANGLE_deg
            time.sleep(waiting_time_s)

        _logger.debug('Stop thread {}'.format(threading.current_thread().name))

    try:
        servo_motion_thread = threading.Thread(target=_move_servo,
                                               name='servo_motion')
        servo_motion_thread.start()

        for data in server.receive():
            data_str = data.decode(_STRING_ENCODING)

            if data_str == 's':
                # Stop signal: do not do anything.
                direction = 0

            elif data_str == 'l':
                # Spin left.
                direction = -1

            elif data_str == 'r':
                # Spin right.
                direction = 1

    except KeyboardInterrupt:
        pass

    # Set direction to None to stop the thread controlling the servo.
    direction = None

    _logger.debug('Stop signal received: bring servo to initial position')
    servo.mid()
    time.sleep(0.5)

    servo.close()
    server.close()
    _logger.info('Stop servo')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _logger = logging.getLogger(__name__)
    _main()
