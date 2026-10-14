#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Generate deterministic *synthetic* test fixtures, not representative benchmarks."""

from __future__ import annotations

import argparse
import random
import zipfile
from pathlib import Path


def generate(output: Path) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    rng = random.Random(0x0A0A2026)
    files: list[Path] = []

    text = output / "repetitive.txt"
    text.write_bytes((b"OHA adaptive compression benchmark line 2026\n" * 2048))
    files.append(text)

    source = output / "sample.rs"
    source.write_text(
        "// Synthetic Rust-like source; generated for compressor testing.\n"
        + "".join(f"pub fn f_{i}(x: u32) -> u32 {{ x.wrapping_mul({i + 1}) }}\n" for i in range(1200)),
        encoding="utf-8",
    )
    files.append(source)

    opaque = output / "uniform.bin"
    opaque.write_bytes(rng.randbytes(96 * 1024))
    files.append(opaque)

    mixed = output / "mixed.bin"
    mixed.write_bytes(b"\x00" * (32 * 1024) + rng.randbytes(32 * 1024) + b"README\n" * 4000)
    files.append(mixed)

    near = output / "near-duplicate.bin"
    payload = bytearray(text.read_bytes())
    payload[len(payload) // 2 : len(payload) // 2 + 11] = b"hello-world"
    near.write_bytes(payload)
    files.append(near)

    already_zip = output / "already-compressed.zip"
    fixed_timestamp = (2020, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(already_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        info = zipfile.ZipInfo("payload.txt", date_time=fixed_timestamp)
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, text.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    files.append(already_zip)
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for path in generate(args.output):
        print(f"{path} {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
