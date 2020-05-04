import argparse
import logging

import cv2
import numpy as np

import common.network as network

logging.basicConfig(level=logging.DEBUG)
_logger = logging.getLogger(__name__)

_CAMERA_ID = 0
_FPS_hz = 30
fx = 10
fy = 10


def _initialize_camera(camera_id):
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        raise RuntimeError('Cannot open camera {}'.format(_CAMERA_ID))

    _logger.debug('Camera {}: opened'.format(_CAMERA_ID))

    ret_fps = cap.set(cv2.CAP_PROP_FPS, _FPS_hz)
    if ret_fps is False:

        raise RuntimeError('Camera {}: failed to set '
                           'FPS to {} '.format(_CAMERA_ID, _FPS_hz))

    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    if actual_fps != _FPS_hz:
        _logger.warning('Camera {}: tried to set FPS to {}, '
                        'but actual FPS is {}'
                        .format(_CAMERA_ID, _FPS_hz, actual_fps))
    else:
        _logger.debug('Camera {}: set FPS to {}'.format(_CAMERA_ID, _FPS_hz))

    return cap


class CameraServer(network.UDPServer):

    def __init__(self, ip, port):
        super().__init__(ip=ip, port=port)

    def run(self):
        try:
            for frame_bytes in self.receive():
                bytes_string = np.fromstring(frame_bytes, np.uint8)
                decoded_frame = cv2.imdecode(bytes_string, cv2.IMREAD_COLOR)
                grayscale_frame = cv2.cvtColor(decoded_frame,
                                               cv2.COLOR_BGR2GRAY)

                # Display the resulting frame
                cv2.imshow('frame', grayscale_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except KeyboardInterrupt:
            pass

        finally:
            # When everything done, release the capture
            self.cap.release()
            cv2.destroyAllWindows()
            self.close()


class CameraClient(network.UDPClient):

    def __init__(self, ip, port, camera_id=_CAMERA_ID):
        super().__init__(ip=ip, port=port)
        self.cap = _initialize_camera(camera_id)

    def run(self):
        try:
            while(True):
                # Capture frame-by-frame
                _ret, frame = self.cap.read()

                image_height, image_width, num_channels = frame.shape
                new_shape = (int(image_width / fx), int(image_height / fy))
                resized_frame = cv2.resize(frame, new_shape)

                _ret, compressed_frame = cv2.imencode('.jpg', resized_frame)
                # print('Compressed frame shape: {}'.format(compressed_frame.shape))
                frame_bytes = compressed_frame.tobytes()

                self.send(data=frame_bytes)

        except KeyboardInterrupt:
            pass

        finally:
            # When everything done, release the capture
            self.cap.release()
            cv2.destroyAllWindows()
            self.close()


def _main():
    parser = argparse.ArgumentParser(description='Try out the network module.')
    parser.add_argument('mode',
                        choices=['c', 's'],
                        help='Run as client (c) or server (s)')
    args = parser.parse_args()

    if args.mode == 'c':
        # Run as client.
        client = CameraClient(ip='192.168.1.50', port=network.PORT, camera_id=0)
        client.run()
    elif args.mode == 's':
        # Run as server.
        server = CameraServer(ip='192.168.1.50', port=network.PORT)
        server.run()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _logger = logging.getLogger(__name__)
    _main()
