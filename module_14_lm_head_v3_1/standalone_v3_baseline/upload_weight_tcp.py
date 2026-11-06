"""Stream only the canonical M14 V2 BF16 weight to the fixed PS DDR window."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import struct
import time
import zlib

MAGIC = 0x5734314D
HEADER = struct.Struct('<8I')
WEIGHT_BYTES = 272269312
CHUNK_BYTES = 1048576
BEGIN, DATA, COMMIT, STATUS = 1, 2, 3, 4


def recv_exact(sock, count):
    out = bytearray()
    while len(out) < count:
        data = sock.recv(count - len(out))
        if not data:
            raise RuntimeError('TCP closed before complete response; weight is unverified')
        out.extend(data)
    return bytes(out)


def exchange(sock, op, seq, offset=0, payload=b'', crc=0, expected_offset=None):
    sock.sendall(HEADER.pack(MAGIC, 1, op, seq, offset, len(payload), WEIGHT_BYTES, crc))
    if payload:
        sock.sendall(payload)
    magic, version, reply_op, reply_seq, next_offset, status, total, actual_crc = HEADER.unpack(recv_exact(sock, 32))
    if (magic, version, reply_op, reply_seq, total) != (MAGIC, 1, op | 0x80000000, seq, WEIGHT_BYTES):
        raise RuntimeError('Invalid TCP loader response identity')
    if status:
        raise RuntimeError(f'PS rejected request: status={status} next={next_offset} crc={actual_crc:08x}')
    if expected_offset is not None and next_offset != expected_offset:
        raise RuntimeError(f'PS offset mismatch: {next_offset} != {expected_offset}')
    if actual_crc != crc:
        raise RuntimeError(f'DDR CRC mismatch: {actual_crc:08x} != {crc:08x}')
    return next_offset


def inspect_weight(weight, manifest):
    meta = json.loads(Path(manifest).read_text(encoding='utf-8-sig'))
    sha = hashlib.sha256()
    crc = 0
    size = 0
    with Path(weight).open('rb') as stream:
        while data := stream.read(CHUNK_BYTES):
            sha.update(data)
            crc = zlib.crc32(data, crc)
            size += len(data)
    if size != WEIGHT_BYTES or sha.hexdigest() != meta['weight_sha256']:
        raise ValueError('Weight size/SHA256 differs from canonical BF16 manifest')
    return sha.hexdigest(), crc


def upload(weight, manifest, host='192.168.8.190', port=1414, timeout=120, progress=True):
    sha, crc = inspect_weight(weight, manifest)
    start = time.perf_counter()
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        exchange(sock, BEGIN, 0, crc=crc, expected_offset=0)
        offset, seq = 0, 1
        with Path(weight).open('rb') as stream:
            while data := stream.read(CHUNK_BYTES):
                exchange(sock, DATA, seq, offset, data, zlib.crc32(data), offset + len(data))
                offset += len(data)
                seq += 1
                if progress and (seq % 16 == 0 or offset == WEIGHT_BYTES):
                    print(f'M14_TCP_PROGRESS bytes={offset}/{WEIGHT_BYTES} elapsed_s={time.perf_counter()-start:.2f}', flush=True)
        if offset != WEIGHT_BYTES:
            raise RuntimeError('Weight changed while uploading')
        # COMMIT performs a fresh full DDR readback, beyond the per-chunk check.
        exchange(sock, COMMIT, seq, offset, crc=crc, expected_offset=WEIGHT_BYTES)
        exchange(sock, STATUS, seq + 1, crc=crc, expected_offset=WEIGHT_BYTES)
    seconds = time.perf_counter() - start
    return {'state': 'PASS', 'host': host, 'port': port, 'bytes': offset,
            'weight_sha256': sha, 'ddr_crc32': f'{crc:08x}', 'elapsed_seconds': seconds,
            'throughput_mib_s': offset / (1 << 20) / seconds,
            'verification': 'host canonical SHA256 + per-chunk DDR CRC32 + full DDR CRC32'}


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='192.168.8.190')
    parser.add_argument('--port', type=int, default=1414)
    parser.add_argument('--weight', type=Path, default=root / 'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin')
    parser.add_argument('--manifest', type=Path, default=root / 'artifacts/module14_v2_assets/manifest.json')
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = upload(args.weight, args.manifest, args.host, args.port, args.timeout)
    except Exception as exc:
        result = {'state': 'FAIL', 'error': str(exc), 'host': args.host, 'port': args.port}
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(f'M14_TCP_WEIGHT_LOAD=FAIL {exc}', flush=True)
        return 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    print('M14_TCP_WEIGHT_LOAD=PASS', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
