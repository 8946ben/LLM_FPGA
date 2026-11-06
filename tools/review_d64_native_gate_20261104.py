"""Replay actual four-state native AXI events. Prepared auditor; EDA not run by import."""
from pathlib import Path
import csv, hashlib, json, re, datetime

BASE = 0x100000000
N = 33554436
EXPECTED_WRITES = [
    (BASE,3,0,1,0xffff), (BASE+0x20000000,3,1,9,0xffff),
    (BASE+1048560,0,1,2,0xffff), (BASE+1048576,1,0,3,0xffff),
    (BASE+16,0,1,4,0x5aa5), (BASE,0,0,8,0),
    (BASE+8192,0,1,6,0x00ff), (BASE+8208,0,0,7,0),
    (BASE+16384,7,1,11,0xffff), (BASE+24576,0,0,13,0xffff),
    (BASE+32768,127,0,21,0xffff)]

def word_bytes(token):
    assert re.fullmatch('[0-9a-fA-FxXzZ]{32}', token), token
    return [token[i:i+2].lower() for i in range(30,-1,-2)]

def pattern(seed, beat):
    return ['%02x' % ((seed*37+beat*19+lane*11)&255) for lane in range(16)]

def replay(path):
    memory = {}; read = None; write = None; pending_b = None
    counters = dict(AR=0,R=0,AW=0,W=0,B=0)
    resets = []; epochs = []; writes = []; canceled_r = 0; canceled_b = 0
    x_reads = 0; done = False; previous_cycle = 0; previous_r = None; consecutive = 0
    for row in csv.reader(Path(path).open()):
        event, cycle = row[0], int(row[1]); assert cycle >= previous_cycle
        previous_cycle = cycle
        if event in counters:
            counters[event] += 1
        if event in ['AR','AW']:
            a, length, ident = int(row[2],16), int(row[3])+1, int(row[4])
            assert ident in [0,1] and a%16 == 0 and 1<=length<=128
            assert BASE <= a < a+16*length <= BASE+16*N
            assert a%4096+16*length <= 4096
            item = dict(address=a,length=length,id=ident,beat=0)
            if event == 'AR':
                assert read is None
                read = item; previous_r = None
            else:
                assert write is None and pending_b is None
                write = item; writes.append((a,length-1,ident))
                assert len(writes) <= len(EXPECTED_WRITES)
                assert writes[-1] == EXPECTED_WRITES[len(writes)-1][:3]
        elif event == 'W':
            assert write is not None
            payload, strobe, last = word_bytes(row[2]), int(row[3],16), int(row[4])
            assert last == int(write['beat'] == write['length']-1)
            seed, expected_mask = EXPECTED_WRITES[len(writes)-1][3:]
            assert payload == pattern(seed,write['beat']) and strobe == expected_mask
            a = write['address']+16*write['beat']
            for lane, byte in enumerate(payload):
                if (strobe >> lane)&1:
                    memory[a+lane] = byte
            write['beat'] += 1
            if last:
                pending_b = write['id']; write = None
        elif event == 'B':
            assert pending_b is not None
            assert int(row[2]) == pending_b and int(row[3]) == 0
            pending_b = None
        elif event == 'R':
            assert read is not None
            payload = word_bytes(row[2]); a = read['address']+16*read['beat']
            assert payload == [memory.get(a+i,'xx') for i in range(16)], (cycle,hex(a),row[2])
            assert int(row[3]) == int(read['beat'] == read['length']-1)
            assert int(row[4]) == read['id'] and int(row[5]) == 0
            if any('x' in x or 'z' in x for x in payload):
                x_reads += 1
            if previous_r is not None and cycle == previous_r+1:
                consecutive += 1
            previous_r = cycle; read['beat'] += 1
            if read['beat'] == read['length']:
                read = None
        elif event == 'RESET':
            resets.append(cycle)
            if len(resets) == 1:
                assert read is not None and read['address'] == BASE and read['beat'] == 0
                assert write is None and pending_b is None
                canceled_r += 1
            elif len(resets) == 2:
                assert read is None and write is None and pending_b == 0
                canceled_b += 1
            else:
                raise AssertionError('Unexpected reset')
            read = write = pending_b = None; previous_r = None
        elif event == 'EPOCH':
            assert read is None and write is None and pending_b is None
            epochs.append(int(row[2])); assert epochs[-1] == len(epochs)-1
        elif event == 'DONE':
            assert not done and read is None and write is None and pending_b is None
            assert [int(x) for x in row[2:]] == [counters[k] for k in ['AR','R','AW','W','B']]
            done = True
        else:
            raise AssertionError('Unknown event '+event)
    assert done and epochs == [0,1,2,3,4] and len(resets) == 2
    assert len(writes) == len(EXPECTED_WRITES) and canceled_r == canceled_b == 1
    assert counters['AW'] == counters['B']+1 and counters['AR'] == 1038
    assert counters['R'] == 131108 and counters['W'] == 152 and counters['AW'] == 11
    assert x_reads == 2 and consecutive > 50000
    assert memory[BASE] != memory[BASE+0x20000000]
    return dict(counters=counters,reset_canceled_reads=canceled_r,reset_canceled_b=canceled_b,
                epochs=epochs,four_state_unwritten_reads=x_reads,consecutive_r_handshakes=consecutive,
                source_trace_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())

if __name__ == '__main__':
    import sys
    assert len(sys.argv) == 2, 'Provide actual completed positive native_wire.csv; this is not a simulator.'
    print(json.dumps(replay(sys.argv[1]),indent=2))
