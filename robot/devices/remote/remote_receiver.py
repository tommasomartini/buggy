import logging
import signal

import common.network as network
import robot.devices.led_status as ls
import robot.devices.remote.common as common
import robot.motion.driver as dvr

_logger = logging.getLogger(__name__)


class RemoteReceiver:
    """Remote controller on robot's side: receives signals from the sender at
    user's side.
    """

    # The remote sends a signal to start the motors and a signal to stop
    # them. If communication breaks in between, risk is that motors will
    # never stop. For this reason, the sender has to keep sending data to
    # the receiver. If data is not received for a large enough interval,
    # the receiver will interpret it as a communication breakdown and will
    # stop the motors automatically.
    _NO_SIGNAL_RECEIVED_TIMEOUT_s = 1.0

    def __init__(self, driver, status_led):
        self._driver = driver
        self._status_led = status_led
        self._server = network.UDPServer(ip=network.RASPBERRYPI_HOSTNAME,
                                         port=network.PORT)

        signal.signal(signal.SIGALRM, self._on_timeout)

        self._status_led.set(ls.Status.WAITING_FOR_REMOTE)

    def _on_timeout(self, signum, frame):
        _logger.warning('Signal from remote stopped unexpectedly: '
                        'stop the motors')
        self._driver.stop()
        self._status_led.set(ls.Status.WAITING_FOR_REMOTE)

    def run(self):
        _logger.debug('{} started'.format(self.__class__.__name__))

        try:
            for data_byte in self._server.receive():
                if data_byte == common.Commands.FORWARD_ON:
                    self._driver.set_command(command_code=dvr.COMMAND_FORWARD,
                                             command_value=True)
                elif data_byte == common.Commands.FORWARD_OFF:
                    self._driver.set_command(command_code=dvr.COMMAND_FORWARD,
                                             command_value=False)
                elif data_byte == common.Commands.BACKWARD_ON:
                    self._driver.set_command(command_code=dvr.COMMAND_BACKWARD,
                                             command_value=True)
                elif data_byte == common.Commands.BACKWARD_OFF:
                    self._driver.set_command(command_code=dvr.COMMAND_BACKWARD,
                                             command_value=False)
                elif data_byte == common.Commands.LEFT_ON:
                    self._driver.set_command(command_code=dvr.COMMAND_LEFT,
                                             command_value=True)
                elif data_byte == common.Commands.LEFT_OFF:
                    self._driver.set_command(command_code=dvr.COMMAND_LEFT,
                                             command_value=False)
                elif data_byte == common.Commands.RIGHT_ON:
                    self._driver.set_command(command_code=dvr.COMMAND_RIGHT,
                                             command_value=True)
                elif data_byte == common.Commands.RIGHT_OFF:
                    self._driver.set_command(command_code=dvr.COMMAND_RIGHT,
                                             command_value=False)
                elif data_byte == common.Commands.TURBO_ON:
                    self._driver.set_command(command_code=dvr.COMMAND_TURBO,
                                             command_value=True)
                elif data_byte == common.Commands.TURBO_OFF:
                    self._driver.set_command(command_code=dvr.COMMAND_TURBO,
                                             command_value=False)

                # Reset the timer to trigger an alarm signal if the next signal
                # from the sender takes too long.
                signal.setitimer(signal.ITIMER_REAL,
                                 self._NO_SIGNAL_RECEIVED_TIMEOUT_s,
                                 0)

                self._status_led.set(ls.Status.READING_REMOTE)

        finally:
            # Disable the alarm.
            signal.setitimer(signal.ITIMER_REAL, 0, 0)
            self._server.close()

        _logger.debug('{} stopped'.format(self.__class__.__name__))

    def close(self):
        self._server.close()
