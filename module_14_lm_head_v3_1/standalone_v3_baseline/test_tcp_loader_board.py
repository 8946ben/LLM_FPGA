"""Deliberate upload failures on a running loader; always fully reload afterward."""
import argparse
import json
from pathlib import Path
import socket
import time
import traceback
import zlib
from upload_weight_tcp import (MAGIC, HEADER, WEIGHT_BYTES, CHUNK_BYTES,
                               BEGIN, DATA, COMMIT, STATUS, recv_exact, inspect_weight)


def connect(host, port):
    # TCP establishment alone is insufficient while the prior connection's FIN
    # is still in flight: this single-client service can reject the new PCB.
    for attempt in range(20):
        sock = socket.create_connection((host, port), timeout=120)
        sock.settimeout(120)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            sock.sendall(HEADER.pack(MAGIC, 1, STATUS, 0, 0, 0, WEIGHT_BYTES, 0))
            response = HEADER.unpack(recv_exact(sock, 32))
            assert response[:4] == (MAGIC, 1, STATUS | 0x80000000, 0), response
            assert response[5] in (0, 4), response
            return sock
        except (ConnectionError, OSError):
            sock.close()
            if attempt == 19:
                raise
            time.sleep(0.1)


def request(sock, op, seq, offset=0, payload=b'', crc=0, expected_status=0,
            expected_offset=None, fragmented=False):
    print(f'M14_TCP_TEST_REQUEST op={op} seq={seq} offset={offset} bytes={len(payload)} fragmented={fragmented}', flush=True)
    wire = HEADER.pack(MAGIC, 1, op, seq, offset, len(payload), WEIGHT_BYTES, crc) + payload
    if fragmented:
        for index in range(0, len(wire), 7):
            sock.sendall(wire[index:index+7])
    else:
        sock.sendall(wire)
    response = HEADER.unpack(recv_exact(sock, 32))
    assert response[:4] == (MAGIC, 1, op | 0x80000000, seq), response
    assert response[5] == expected_status and response[6] == WEIGHT_BYTES, response
    if expected_offset is not None:
        assert response[4] == expected_offset, response
    if expected_status == 0:
        assert response[7] == crc, response
    return response


def not_ready(host, port):
    # A disconnected upload may take a few packet loops to release its PCB.
    for attempt in range(20):
        try:
            with connect(host, port) as sock:
                response = request(sock, STATUS, 999, expected_status=4)
            return response
        except (ConnectionError, OSError):
            if attempt == 19:
                raise
            time.sleep(0.1)


def expect_closed(sock, wire):
    sock.settimeout(5)
    try:
        sock.sendall(wire)
        data = sock.recv(32)
        assert data == b'', f'invalid request was accepted: {data.hex()}'
    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
        return
    # A timeout must fail the test: it is not evidence of explicit rejection.


def run(args):
    results = []
    sha, crc = inspect_weight(args.weight, args.manifest)

    def passed(name):
        results.append({'test': name, 'state': 'PASS'})
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({'state': 'RUNNING', 'tests': results}, indent=2))
        print(f'M14_TCP_FAULT_PASS test={name}', flush=True)

    with connect(args.host, args.port) as sock:
        request(sock, BEGIN, 0, crc=crc)
        # Bad payload CRC must return BAD_CRC, and must not advance DDR offset.
        data = bytes(range(64))
        request(sock, DATA, 1, payload=data, crc=zlib.crc32(data) ^ 1,
                expected_status=3, expected_offset=0)
        request(sock, STATUS, 2, expected_status=4, expected_offset=0)
    passed('bad_chunk_crc_invalidates_image')

    with connect(args.host, args.port) as sock:
        request(sock, BEGIN, 0, crc=crc, fragmented=True)
        request(sock, DATA, 1, payload=data, crc=zlib.crc32(data),
                expected_offset=64, fragmented=True)
        request(sock, STATUS, 2, expected_status=4, expected_offset=64)
        expect_closed(sock, HEADER.pack(MAGIC, 1, DATA, 1, 0, 64, WEIGHT_BYTES, zlib.crc32(data)))
    not_ready(args.host, args.port)
    passed('fragmented_frame_and_duplicate_rejection')

    with connect(args.host, args.port) as sock:
        request(sock, BEGIN, 0, crc=crc)
        expect_closed(sock, HEADER.pack(MAGIC, 1, DATA, 1, 0, CHUNK_BYTES + 1, WEIGHT_BYTES, 0))
    not_ready(args.host, args.port)
    passed('oversized_chunk_rejection')

    with connect(args.host, args.port) as sock:
        request(sock, BEGIN, 0, crc=crc)
        expect_closed(sock, HEADER.pack(MAGIC, 1, COMMIT, 1, 0, 0, WEIGHT_BYTES, crc))
    not_ready(args.host, args.port)
    passed('truncated_commit_rejection')

    with connect(args.host, args.port) as sock:
        request(sock, BEGIN, 0, crc=crc)
        sock.sendall(HEADER.pack(MAGIC, 1, DATA, 1, 0, CHUNK_BYTES, WEIGHT_BYTES, 0))
        sock.sendall(b'\0' * 4096)
        # Graceful EOF in the middle of a payload must invalidate that upload.
    not_ready(args.host, args.port)
    passed('mid_payload_disconnect_invalidates_image')

    if args.full_commit_fault:
        # Correct per-block payloads, wrong whole-image expected CRC. COMMIT must
        # reject the fresh full DDR scan rather than merely echoing the header.
        with connect(args.host, args.port) as sock:
            wrong_crc = crc ^ 1
            request(sock, BEGIN, 0, crc=wrong_crc)
            offset, seq = 0, 1
            with args.weight.open('rb') as stream:
                while data := stream.read(CHUNK_BYTES):
                    request(sock, DATA, seq, offset, data, zlib.crc32(data),
                            expected_offset=offset + len(data))
                    offset += len(data)
                    seq += 1
                    if seq % 32 == 0:
                        print(f'M14_TCP_FAULT_PROGRESS bytes={offset}/{WEIGHT_BYTES}', flush=True)
            response = request(sock, COMMIT, seq, offset, crc=wrong_crc,
                               expected_status=5, expected_offset=WEIGHT_BYTES)
            assert response[7] == crc, response
            request(sock, STATUS, seq+1, expected_status=4)
        passed('full_ddr_crc_rejects_wrong_expected_crc')
    return {'state': 'PASS', 'tests': results, 'weight_sha256': sha,
            'requires_full_reload': True, 'host': args.host, 'port': args.port}


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='192.168.8.190')
    parser.add_argument('--port', type=int, default=1414)
    parser.add_argument('--weight', type=Path, default=root/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin')
    parser.add_argument('--manifest', type=Path, default=root/'artifacts/module14_v2_assets/manifest.json')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--full-commit-fault', action='store_true')
    args = parser.parse_args()
    try:
        result = run(args)
    except Exception as exc:
        result = {'state': 'FAIL', 'error': str(exc), 'traceback': traceback.format_exc(),
                  'requires_full_reload': True}
        print(f'M14_TCP_FAULT_TEST=FAIL {exc}', flush=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    print('M14_TCP_FAULT_TEST=' + result['state'], flush=True)
    return 0 if result['state'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
