import argparse
import logging
import math

import cv2
import numpy as np

import common.network as network

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

_CAMERA_ID = 0
_FPS_hz = 30

# How many bytes are reserved for the image id. The image ids will span the
# range [0, 2^(N * 8) - 1] with N number of bytes. This id will cycle.
_IMAGE_ID_BYTES = 1

# How many bytes are reserved for the chunk id. Each image will be split into
# chunks of bytes and each of them will have an incremental id to allow the
# receiver to correctly reconstruct the message.
# Although the UDP payload can be up to 65507 bytes, common networks allows a
# maximum MTU of around 1500 bytes. By using 65536 chunks of 1500 bytes we could
# send an image of 98 Megabytes, which is more than enough for this case.
_CHUNK_ID_BYTES = 2

_BYTE_ORDER = 'big'

_BYTES_CHUNK = network.BUFFER_SIZE - _IMAGE_ID_BYTES - 2 * _CHUNK_ID_BYTES


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
        self._image_id = -1
        self._chunk_counter = 0
        self._chunks = []

    @staticmethod
    def _decode_header(frame_bytes):
        """Decodes the header of a received packet and returns the decoded
        information as a tuple.

        Args:
            frame_bytes (bytes): Raw bytes received from the network.

        Returns:
            A tuple containing item id, chunk id, number of expected chunks for
            this item and the index where the payload starts.
        """
        start = 0
        item_id = int.from_bytes(frame_bytes[start: start + _IMAGE_ID_BYTES],
                                 byteorder=_BYTE_ORDER)
        start += _IMAGE_ID_BYTES

        chunk_id = int.from_bytes(
            frame_bytes[start: start + _CHUNK_ID_BYTES],
            byteorder=_BYTE_ORDER)
        start += _CHUNK_ID_BYTES

        num_chunks = int.from_bytes(
            frame_bytes[start: start + _CHUNK_ID_BYTES],
            byteorder=_BYTE_ORDER)
        start += _CHUNK_ID_BYTES

        return item_id, chunk_id, num_chunks, start

    def _reconstruct_image(self):
        """Reconstructs an image putting together the chunks of bytes received.
        """
        buffer = b''.join(self._chunks)
        bytes_string = np.frombuffer(buffer, np.uint8)
        decoded_frame = cv2.imdecode(bytes_string, cv2.IMREAD_COLOR)
        return decoded_frame

    def run(self):
        try:
            for frame_bytes in self.receive():
                image_id, chunk_id, num_chunks, start = \
                    self._decode_header(frame_bytes)

                if image_id > self._image_id:
                    # New image: drop the current one, if we have one already.
                    if self._image_id < 0:
                        _logger.debug('New frame')
                    else:
                        _logger.debug('Frame drop')

                    self._image_id = image_id
                    self._chunk_counter = 0
                    self._chunks = [None] * num_chunks

                elif image_id < self._image_id:
                    # Frame from past image: ignore.
                    continue

                payload = frame_bytes[start:]
                self._chunks[chunk_id] = payload
                self._chunk_counter += 1

                if self._chunk_counter == num_chunks:
                    self._image_id = -1
                    self._chunk_counter = 0
                    frame = self._reconstruct_image()
                    cv2.imshow('Frame', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

        except KeyboardInterrupt:
            pass

        finally:
            cv2.destroyAllWindows()
            self.close()


class CameraClient(network.UDPClient):

    def __init__(self, ip, port, camera_id=_CAMERA_ID):
        super().__init__(ip=ip, port=port)
        self.cap = _initialize_camera(camera_id)
        self._image_id = 0

    @staticmethod
    def _process_image(frame):
        """Transforms a numpy array representing an image into a bytes object
        ready to be sent over the network.

        Args:
            frame (:obj:`numpy.array`): Numpy array with shape
                (height, width, channels).

        Returns:
            A bytes object.
        """
        _ret, compressed_frame = cv2.imencode('.jpg', frame)
        frame_bytes = compressed_frame.tobytes()
        return frame_bytes

    def _get_header_generator(self, num_chunks):
        """Returns a function that generates the header for the current chunk.

        Args:
            num_chunks (int): How many chunks this item will be split in.

        Returns:
            A function in the form f(chunk_id) -> bytes, that takes the id of
            the current chunk of data as argument and returns a bytes object
            representing the header for this chunk.
        """
        bnum_chunks = int.to_bytes(num_chunks, _CHUNK_ID_BYTES, byteorder=_BYTE_ORDER)
        bimage_id = int.to_bytes(self._image_id, _IMAGE_ID_BYTES, byteorder=_BYTE_ORDER)

        def _generate_header(chunk_id):
            bchunk_id = int.to_bytes(chunk_id, _CHUNK_ID_BYTES, byteorder=_BYTE_ORDER)
            header = bimage_id + bchunk_id + bnum_chunks
            return header

        return _generate_header

    def run(self):
        try:
            while True:
                _ret, frame = self.cap.read()
                frame_bytes = self._process_image(frame)
                num_bytes = len(frame_bytes)
                num_chunks = math.ceil(num_bytes / _BYTES_CHUNK)

                generate_header = \
                    self._get_header_generator(num_chunks=num_chunks)
                for chunk_id in range(num_chunks):
                    start_idx = chunk_id * _BYTES_CHUNK
                    end_idx = min(num_bytes, (chunk_id + 1) * _BYTES_CHUNK)
                    payload = frame_bytes[start_idx: end_idx]
                    header = generate_header(chunk_id)
                    chunk_bytes = header + payload
                    self.send(data=chunk_bytes)

                self._image_id = \
                    (self._image_id + 1) % (2 ** (_IMAGE_ID_BYTES * 8))

        except KeyboardInterrupt:
            pass

        finally:
            self.cap.release()
            self.close()


def _main():
    parser = argparse.ArgumentParser(
        description='Try out the video stream module.')
    parser.add_argument('mode',
                        choices=['c', 's'],
                        help='Run as client (c) or server (s)')
    parser.add_argument('ip',
                        type=str,
                        help='IP address of the server')
    args = parser.parse_args()

    if args.mode == 'c':
        # Run as client.
        client = \
            CameraClient(ip=args.ip, port=network.PORT, camera_id=_CAMERA_ID)
        client.run()

    elif args.mode == 's':
        # Run as server.
        server = CameraServer(ip=args.ip, port=network.PORT)
        server.run()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _logger = logging.getLogger(__name__)
    _main()
