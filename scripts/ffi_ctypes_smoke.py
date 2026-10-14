#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Cross-platform Python foreign-caller verification of the experimental C ABI."""

import ctypes
import os
import pathlib
import sys


class Analysis(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("version", ctypes.c_uint32),
        ("input_bytes", ctypes.c_uint64),
        ("sampled_bytes", ctypes.c_uint64),
        ("entropy_bits_per_byte", ctypes.c_double),
        ("ascii_ratio", ctypes.c_double),
        ("zero_ratio", ctypes.c_double),
        ("unique_byte_values", ctypes.c_uint32),
        ("content_hint", ctypes.c_uint32),
        ("reserved", ctypes.c_uint64 * 2),
    ]


def main() -> None:
    root = pathlib.Path(__file__).resolve().parents[1]
    if sys.platform == "win32":
        library_path = root / "target/debug/oha_ffi.dll"
    elif sys.platform == "darwin":
        library_path = root / "target/debug/liboha_ffi.dylib"
    else:
        library_path = root / "target/debug/liboha_ffi.so"
    assert library_path.is_file(), library_path
    lib = ctypes.CDLL(str(library_path))
    lib.oha_api_version.restype = ctypes.c_uint32
    lib.oha_analyze_bytes_v1.restype = ctypes.c_int32
    lib.oha_analyze_bytes_v1.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.POINTER(Analysis)]
    assert lib.oha_api_version() == 1
    assert ctypes.sizeof(Analysis) == 72
    assert Analysis.content_hint.offset == 52
    assert Analysis.reserved.offset == 56

    def measure(content: bytes) -> Analysis:
        data = ctypes.create_string_buffer(content) if content else None
        output = Analysis(struct_size=ctypes.sizeof(Analysis), version=1)
        code = lib.oha_analyze_bytes_v1(data, len(content), ctypes.byref(output))
        assert code == 0, code
        assert output.sampled_bytes == len(content)
        assert output.input_bytes == len(content)
        assert list(output.reserved) == [0, 0]
        return output

    assert measure(b"").content_hint == 0
    assert measure("Hello, OHA!\n".encode()).content_hint == 1
    assert measure(bytes(4096)).content_hint == 2
    assert lib.oha_analyze_bytes_v1(None, 0, None) == 1
    output = Analysis(struct_size=72, version=1)
    assert lib.oha_analyze_bytes_v1(None, 1, ctypes.byref(output)) == 2
    assert lib.oha_analyze_bytes_v1(None, 196609, ctypes.byref(output)) == 3
    output.version = 2
    assert lib.oha_analyze_bytes_v1(None, 0, ctypes.byref(output)) == 4
    print("OHA C ABI foreign-caller smoke PASS", os.name, sys.platform)


if __name__ == "__main__":
    main()
