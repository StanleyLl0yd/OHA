# SPDX-License-Identifier: MPL-2.0
"""Bounded READ-ONLY RFC 8949 deterministic CBOR metadata proposal, not .oha decoding."""
from __future__ import annotations
import unicodedata

MAX_BYTES = 4 * 1024 * 1024
MAX_ITEMS = 100_000
MAX_DEPTH = 7
MAX_BLOCK = 16 * 1024 * 1024

class ProposalError(ValueError):
    pass

class Reader:
    def __init__(self, raw: bytes, limit: int, items: int):
        if not isinstance(raw, bytes) or limit < 0 or items < 1 or len(raw) > limit:
            raise ProposalError("metadata resource budget")
        self.raw, self.pos, self.items, self.count = raw, 0, items, 0

    def take(self, n: int) -> bytes:
        if n > len(self.raw) - self.pos:
            raise ProposalError("truncated CBOR")
        value = self.raw[self.pos:self.pos + n]
        self.pos += n
        return value

    def arg(self, small: int) -> int:
        if small < 24:
            return small
        widths = {24: (1, 24), 25: (2, 256), 26: (4, 65536), 27: (8, 1 << 32)}
        if small not in widths:
            raise ProposalError("indefinite or reserved CBOR argument")
        width, minimum = widths[small]
        value = int.from_bytes(self.take(width), "big")
        if value < minimum:
            raise ProposalError("non-minimal CBOR integer or length")
        return value

    def value(self, depth: int = 0):
        self.count += 1
        if depth > MAX_DEPTH or self.count > self.items:
            raise ProposalError("CBOR nesting/item budget")
        initial = self.take(1)[0]
        major, info = initial >> 5, initial & 31
        if major not in (0, 2, 3, 4):
            raise ProposalError("prohibited CBOR type")
        n = self.arg(info)
        if major == 0:
            return n
        if major in (2, 3):
            b = self.take(n)
            if major == 2:
                return b
            try:
                text = b.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ProposalError("invalid UTF-8") from exc
            if unicodedata.normalize("NFC", text) != text:
                raise ProposalError("non-NFC CBOR text")
            return text
        if n > self.items - self.count:
            raise ProposalError("CBOR array item budget")
        return [self.value(depth + 1) for _ in range(n)]

def parse(raw: bytes, *, max_bytes: int = MAX_BYTES, max_items: int = MAX_ITEMS):
    reader = Reader(raw, max_bytes, max_items)
    value = reader.value()
    if reader.pos != len(raw):
        raise ProposalError("trailing CBOR metadata")
    return value

def unsigned(value, name: str, cap: int = (1 << 64) - 1) -> int:
    if type(value) is not int or not 0 <= value <= cap:
        raise ProposalError("invalid " + name)
    return value

def root(raw: bytes, label: str):
    obj = parse(raw)
    if type(obj) is not list or len(obj) != 2 or obj[0] != 1 or type(obj[1]) is not list:
        raise ProposalError(label + ": incompatible metadata schema")
    return obj[1]

def manifest(raw: bytes):
    """Proposed MNFT [1, [[path, kind, size, [[block_id, file_offset, length],...]],...]]."""
    result, previous = [], None
    for row in root(raw, "MNFT"):
        if type(row) is not list or len(row) != 4:
            raise ProposalError("MNFT row shape")
        path, kind, size, segments = row
        if type(path) is not str or not path:
            raise ProposalError("MNFT empty path")
        key = path.encode("utf-8")
        if previous is not None and key <= previous:
            raise ProposalError("MNFT duplicate or unsorted path")
        previous = key
        unsigned(kind, "entry kind", 1)
        unsigned(size, "file size", (1 << 63) - 1)
        if type(segments) is not list:
            raise ProposalError("MNFT segment shape")
        cursor = 0
        for segment in segments:
            if kind != 0 or type(segment) is not list or len(segment) != 3:
                raise ProposalError("MNFT illegal segment")
            bid, offset, length = segment
            unsigned(bid, "block id")
            unsigned(offset, "file offset")
            unsigned(length, "decoded length", MAX_BLOCK)
            if bid == 0 or length == 0 or offset != cursor or length > size - cursor:
                raise ProposalError("MNFT segment coverage")
            cursor += length
        if cursor != size or (kind == 1 and (size != 0 or segments)):
            raise ProposalError("MNFT file size / directory mismatch")
        result.append((path, kind, size, segments))
    return result

def index(raw: bytes):
    """Proposed INDX [1, [[block_id, frame_at, frame_bytes, decoded_bytes, codec],...]]."""
    records, previous = {}, 0
    for row in root(raw, "INDX"):
        if type(row) is not list or len(row) != 5:
            raise ProposalError("INDX row shape")
        bid, offset, frame_bytes, decoded, codec = row
        for name, val in (("block id", bid), ("frame offset", offset),
                          ("frame bytes", frame_bytes), ("decoded bytes", decoded)):
            unsigned(val, name, MAX_BLOCK if name == "decoded bytes" else (1 << 64) - 1)
        unsigned(codec, "codec", 1)
        if bid <= previous or offset < 64 or frame_bytes <= 80:
            raise ProposalError("INDX record order/range")
        if codec == 0 and frame_bytes - 80 != decoded:
            raise ProposalError("INDX STORE length mismatch")
        records[bid] = {"offset": offset, "frame_bytes": frame_bytes,
                        "decoded_bytes": decoded, "codec": codec}
        previous = bid
    return records

def check_references(mrows, irows):
    """Provisional no-dedup constraint; does NOT verify physical archive frames."""
    used = set()
    for _, kind, _, parts in mrows:
        if kind:
            continue
        for bid, _, length in parts:
            if bid not in irows or bid in used:
                raise ProposalError("missing or repeated DATA reference")
            if length != irows[bid]["decoded_bytes"]:
                raise ProposalError("manifest/index decoded length mismatch")
            used.add(bid)
    if used != set(irows):
        raise ProposalError("orphan DATA index")
    return len(used)
