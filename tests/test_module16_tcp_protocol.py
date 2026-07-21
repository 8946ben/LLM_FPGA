import socket
import threading
import unittest

import numpy as np

from module16_lm_head_hls.net.cpu_client import LmHeadClient
from module16_lm_head_hls.net.fpga_server_emulator import LmHeadBoardEmulator
from module16_lm_head_hls.net.lmh_protocol import ProtocolError, recv_frame, send_frame


def connected_client(emulator: LmHeadBoardEmulator):
    client_socket, server_socket = socket.socketpair()
    thread = threading.Thread(
        target=emulator.serve_connection, args=(server_socket,), daemon=True
    )
    thread.start()
    return LmHeadClient(client_socket), thread


def synthetic_weight() -> np.ndarray:
    return np.asarray(
        [
            [1.0, 0.0, 0.0, 1.5],
            [0.8, 0.0, 0.0, 1.5],
            [-1.0, 0.5, 1.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
        ],
        dtype=np.float16,
    )


class TestModule16TcpProtocol(unittest.TestCase):
    def test_frame_round_trip(self):
        left, right = socket.socketpair()
        try:
            send_frame(left, 3, 17, 5, b"payload")
            frame = recv_frame(right)
            self.assertEqual(
                (frame.opcode, frame.request_id, frame.flags, frame.payload),
                (3, 17, 5, b"payload"),
            )
        finally:
            left.close()
            right.close()

    def test_crc_error_is_rejected(self):
        left, right = socket.socketpair()
        try:
            from module16_lm_head_hls.net.lmh_protocol import HEADER, MAGIC, VERSION

            left.sendall(HEADER.pack(MAGIC, VERSION, 3, 1, 0, 1, 0) + b"x")
            with self.assertRaisesRegex(ProtocolError, "CRC32 mismatch"):
                recv_frame(right)
        finally:
            left.close()
            right.close()

    def test_weight_upload_ping_and_repetition_argmax(self):
        emulator = LmHeadBoardEmulator()
        client, thread = connected_client(emulator)
        try:
            client.load_weight(synthetic_weight(), chunk_bytes=10)
            ping = client.ping()
            self.assertEqual(
                (ping.hidden_size, ping.vocab_size, ping.weight_bytes), (4, 4, 32)
            )
            hidden = np.asarray([1.0, 0.5, -1.0, 2.0], dtype=np.float16)
            history = np.asarray([1], dtype=np.uint32)
            result = client.run_token(
                hidden,
                history,
                vocab_size=4,
                repetition_penalty=1.1,
                return_logits=True,
            )
            self.assertEqual(result.token_id, 1)
            np.testing.assert_allclose(
                result.raw_logits, [4.0, 3.8, -1.75, 0.5], atol=0.01
            )
        finally:
            client.close()
            thread.join(timeout=2)

    def test_argmax_tie_keeps_lowest_token_id(self):
        weight = np.asarray([[1.0], [1.0], [0.5]], dtype=np.float16)
        client, thread = connected_client(LmHeadBoardEmulator(weight))
        try:
            result = client.run_token(
                np.asarray([2.0], dtype=np.float16),
                np.asarray([0], dtype=np.uint32),
                vocab_size=3,
                enable_repetition_penalty=False,
            )
            self.assertEqual(result.token_id, 0)
        finally:
            client.close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
