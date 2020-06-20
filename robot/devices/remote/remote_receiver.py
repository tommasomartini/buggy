import logging

import common.network as network
import robot.devices.remote.common as common
import robot.motion.driver as dvr

_logger = logging.getLogger(__name__)


class RemoteReceiver:
    """Remote controller on robot's side: receives signals from the sender at
    user's side.
    """

    def __init__(self, driver):
        self._driver = driver
        self._server = network.UDPServer(ip=network.RASPBERRYPI_HOSTNAME,
                                         port=network.PORT)

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

        finally:
            self._server.close()

        _logger.debug('{} stopped'.format(self.__class__.__name__))
