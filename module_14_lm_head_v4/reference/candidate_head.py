"""Exact candidate-row projection using the accepted dense arithmetic order.

This is a CPU experiment, not a selector, HLS kernel, or FPGA timing model.
Only requested canonical BF16 rows are gathered. Unselected scores are absent.
"""
from __future__ import annotations

import struct
import zlib
import numpy as np

from .numeric_contract import compute_raw_logits, output_crc32

TABLE_VERSION = 1
TABLE_HEADER = struct.Struct('<4sHHII')
RECORD_DTYPE = np.dtype([('global_id', '<u4'), ('raw_score', '<f4')])


def candidate_ids(values, vocab_size: int, *, require_sorted=True) -> np.ndarray:
    """Reject malformed input instead of silently truncating, deduping or clipping."""
    ids = np.asarray(values)
    if not isinstance(vocab_size, int) or isinstance(vocab_size, bool) or not 0 < vocab_size <= 0xffffffff:
        raise ValueError('vocab_size must fit uint32 and be positive')
    if ids.ndim != 1 or not 0 < ids.size <= vocab_size:
        raise ValueError('candidate count must be in [1,V], one dimension')
    if ids.dtype.kind not in 'iu':
        raise ValueError('candidate IDs must be integers (not floats or bools)')
    if np.any(ids < 0) or np.any(ids >= vocab_size):
        raise ValueError('global token ID out of range')
    ids = ids.astype(np.uint32)
    ordered = np.sort(ids)
    if np.any(ordered[1:] == ordered[:-1]):
        raise ValueError('duplicate global token IDs')
    if require_sorted and not np.array_equal(ids, ordered):
        raise ValueError('candidate table must be sorted by global ID')
    return ids


def encode_candidate_table(ids, vocab_size: int) -> bytes:
    ids = candidate_ids(ids, vocab_size)
    return TABLE_HEADER.pack(b'M4ID', TABLE_VERSION, 4, len(ids), vocab_size) + ids.astype('<u4').tobytes()


def decode_candidate_table(data: bytes, expected_vocab_size: int) -> np.ndarray:
    if len(data) < TABLE_HEADER.size:
        raise ValueError('truncated candidate header')
    magic, version, entry_bytes, count, vocab = TABLE_HEADER.unpack_from(data)
    if magic != b'M4ID' or version != TABLE_VERSION or entry_bytes != 4:
        raise ValueError('candidate table identity/version mismatch')
    if vocab != expected_vocab_size or len(data) != TABLE_HEADER.size + count * 4:
        raise ValueError('candidate table capacity/length mismatch')
    return candidate_ids(np.frombuffer(data, dtype='<u4', offset=TABLE_HEADER.size), vocab)


def select_candidate(raw, ids, vocab_size: int, history=None, *, penalty=1.0, enable_penalty=True):
    """Apply policy using global IDs, with an explicit lower-global-ID tie rule."""
    ids = candidate_ids(ids, vocab_size, require_sorted=False)
    raw = np.asarray(raw, dtype=np.float32)
    if raw.shape != ids.shape or not np.all(np.isfinite(raw)):
        raise FloatingPointError('candidate raw scores must be finite and match K')
    scores = raw.copy()
    if enable_penalty:
        p = np.float32(penalty)
        if not np.isfinite(p) or p < 1:
            raise ValueError('penalty must be finite and >=1')
        words = np.asarray(history)
        if words.ndim != 1 or words.dtype.kind not in 'iu' or words.size < (vocab_size + 31)//32:
            raise ValueError('history must cover the global vocabulary')
        if np.any(words < 0) or np.any(words > 0xffffffff):
            raise ValueError('history word out of uint32 range')
        words = words.astype(np.uint32)
        seen = ((words[ids >> 5] >> (ids & 31)) & 1).astype(bool)
        negative = seen & (scores < np.float32(0))
        positive = seen & ~negative
        with np.errstate(over='ignore'):
            scores[negative] = np.multiply(scores[negative], p, dtype=np.float32)
            scores[positive] = np.divide(scores[positive], p, dtype=np.float32)
    # Index order is not a tie-break contract. Use global token IDs explicitly.
    winner = int(np.min(ids[scores == np.max(scores)]))
    slot = int(np.flatnonzero(ids == winner)[0])
    return scores, winner, np.float32(scores[slot])


def run_candidate_head(hidden_bf16, weight_bf16, ids, history=None, *,
                       penalty=1.1, enable_penalty=True, token_block=1024):
    weights = np.asarray(weight_bf16)
    hidden = np.asarray(hidden_bf16)
    if weights.ndim != 2 or weights.dtype.kind != 'u' or weights.dtype.itemsize != 2:
        raise ValueError('weights must be canonical uint16 BF16 [V,H]')
    vocab, width = weights.shape
    if hidden.ndim != 1 or hidden.size != width or hidden.dtype.kind != 'u' or hidden.dtype.itemsize != 2:
        raise ValueError('hidden must be uint16 BF16 [H]')
    if not isinstance(token_block, int) or isinstance(token_block, bool) or token_block <= 0:
        raise ValueError('token_block must be a positive integer')
    ids = candidate_ids(ids, vocab)
    raw = np.empty(len(ids), dtype=np.float32)
    # Never compute the full matrix first and filter its output afterward.
    for start in range(0, len(ids), token_block):
        stop = min(start + token_block, len(ids))
        raw[start:stop] = compute_raw_logits(hidden, weights[ids[start:stop]], token_block=token_block)
    scores, winner, score = select_candidate(raw, ids, vocab, history,
        penalty=penalty, enable_penalty=enable_penalty)
    records = np.empty(len(ids), dtype=RECORD_DTYPE)
    records['global_id'], records['raw_score'] = ids, raw
    return dict(ids=ids, raw_scores=raw, policy_scores=scores, records=records,
        selected_token=winner, selected_score_bits=int(score.view(np.uint32)),
        output_crc=output_crc32(winner, score),
        candidate_records_crc32=zlib.crc32(records.tobytes()) & 0xffffffff,
        output_coverage='ALL_ROWS' if len(ids) == vocab else 'CANDIDATES_ONLY',
        computed_rows=len(ids), logical_weight_bytes=len(ids)*width*2,
        logical_candidate_id_bytes=len(ids)*4,
        logical_history_block_bytes=len(np.unique(ids >> 7))*16 if enable_penalty else 0)
