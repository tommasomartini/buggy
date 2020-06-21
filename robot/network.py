import argparse
import logging
import socket

RASPBERRYPI_HOSTNAME = 'raspberrypi.local'
PORT = 7771
BUFFER_SIZE = 1024

_logger = logging.getLogger(__name__)


class _UDPSocket:

    def __init__(self, ip, port):
        self._ip = ip
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def close(self):
        self._socket.close()
        _logger.info('UDP socket closed')


class UDPClient(_UDPSocket):

    def send(self, data):
        num_sent_bytes = self._socket.sendto(data, (self._ip, self._port))
        _logger.debug('Sent {} bytes '
                      'to {}:{}'.format(num_sent_bytes, self._ip, self._port))


class UDPServer(_UDPSocket):

    def __init__(self, ip, port):
        super().__init__(ip, port)
        self._socket.bind((ip, port))
        _logger.info('UDP Server bound to {}:{}'.format(self._ip, self._port))

    def receive(self):
        while True:
            data, from_address = self._socket.recvfrom(BUFFER_SIZE)
            _logger.debug('Received {} bytes '
                          'from {}'.format(len(data), from_address))
            yield data


def _main():
    parser = argparse.ArgumentParser(description='Try out the network module.')
    parser.add_argument('mode',
                        choices=['c', 's'],
                        help='Run as client (c) or server (s)')
    args = parser.parse_args()

    if args.mode == 'c':
        # Run as client.
        client = UDPClient(ip=RASPBERRYPI_HOSTNAME, port=PORT)
        client.send(bytes('Hello Pi!', 'utf-8'))
        client.close()
    elif args.mode == 's':
        # Run as server.
        server = UDPServer(ip=RASPBERRYPI_HOSTNAME, port=PORT)
        try:
            for data in server.receive():
                print(data.decode('utf-8'))
        except KeyboardInterrupt:
            server.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _logger = logging.getLogger(__name__)
    _main()
