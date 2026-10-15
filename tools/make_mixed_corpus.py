#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Generate an independently-owned SYNTHETIC mixed-workload compression corpus.

This is a repeatable benchmark smoke workload, NOT real customer/VM/media data.
Only the JSON manifest and performance results should be uploaded from CI.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import random
import sqlite3
import zipfile

SEED = 0x0A2026
IMAGE_BYTES = 8 * 1024 * 1024


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def generate(output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError("output must be empty: avoid mixing or overwriting corpora")
    output.mkdir(parents=True, exist_ok=True)
    corpus = output / "files"
    corpus.mkdir()
    rng = random.Random(SEED)
    labels: dict[str, str] = {}

    def mark(path: Path, label: str):
        labels[path.relative_to(corpus).as_posix()] = label

    text = corpus / "structured.csv"
    text.write_text("id,category,description\n" + "".join(
        f"{i},group_{i % 19},Synthetic OHA record {i % 100} with recurring words\n"
        for i in range(16000)), encoding="utf-8")
    mark(text, "repeated structured text")

    noisy = corpus / "uniform.bin"
    noisy.write_bytes(rng.randbytes(1024 * 1024))
    mark(noisy, "deterministic pseudo-random high entropy")

    image = corpus / "sparse-disk.img"
    with image.open("wb") as stream:
        stream.truncate(IMAGE_BYTES)
        for at in (0, 3 * 1024 * 1024, IMAGE_BYTES - 32768):
            stream.seek(at)
            stream.write(rng.randbytes(32768))
    mark(image, "sparse VM-like byte layout (not actual VM data)")

    previous = corpus / "snapshot-before.bin"
    base = bytearray((b"synthetic application record\n" * 36000)[:1024 * 1024])
    previous.write_bytes(base)
    mark(previous, "versioned duplicate before")
    for start in (9000, 160000, 600000):
        base[start:start + 8192] = rng.randbytes(8192)
    after = corpus / "snapshot-after.bin"
    after.write_bytes(base)
    mark(after, "versioned duplicate after")

    database = corpus / "sample.sqlite"
    with sqlite3.connect(database) as db:
        db.execute("PRAGMA page_size=4096")
        db.execute("CREATE TABLE synthetic_events (id INTEGER PRIMARY KEY, category TEXT, body TEXT, noise BLOB)")
        db.executemany("INSERT INTO synthetic_events VALUES (?, ?, ?, ?)", (
            (i, f"class{i % 17}", "generated text " * (i % 11 + 1),
             rng.randbytes(64 + (i % 4) * 64)) for i in range(2400)
        ))
        db.commit()
    mark(database, "SQLite test database generated with Python stdlib")

    archive = corpus / "already-compressed.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, contents in (("text.csv", text.read_bytes()),
                               ("uniform.bin", noisy.read_bytes())):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, contents, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    mark(archive, "already-compressed ZIP")

    compressed = corpus / "already-compressed.gz"
    with compressed.open("wb") as stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=stream, mtime=0) as gz:
            gz.write(noisy.read_bytes())
    mark(compressed, "already-compressed GZIP")

    tiny = corpus / "tiny-tree"
    tiny.mkdir()
    for i in range(128):
        file = tiny / f"{i:03}.json"
        file.write_text(json.dumps({"n": i, "kind": i % 7, "value": "same text " * 4},
                                   sort_keys=True) + "\n", encoding="utf-8")
        mark(file, "many small JSON records")

    entries = []
    for rel in sorted(labels):
        source = corpus / rel
        entries.append({
            "path": rel, "category": labels[rel], "bytes": source.stat().st_size,
            "sha256": file_sha256(source),
        })
    manifest = {
        "schema_version": 1,
        "kind": "OWNED_SYNTHETIC_MIXED_CORPUS_NOT_REAL_OR_OHA_PERFORMANCE",
        "generator_seed": SEED,
        "generator_python_sqlite_version": sqlite3.sqlite_version,
        "file_count": len(entries),
        "total_bytes": sum(x["bytes"] for x in entries),
        "limits": {"synthetic_disk_image_bytes": IMAGE_BYTES},
        "files": entries,
        "warning": "Artificial workload only; never label as customer datasets, VM images, medical images or real media.",
    }
    (output / "corpus-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = generate(args.output)
    print(f"Generated {result['file_count']} synthetic files: {result['total_bytes']} bytes")


if __name__ == "__main__":
    main()
