# M0 smoke test results: six synthetic files

Generated using `tools/make_corpus.py` and probed with `tools/benchmark.py` (3 repetitions, each verified by SHA-256 after full independent decompression). This is an instrumentation proof, **not** a real workload benchmark or performance claim about OHA.

| Fixture | Input bytes | ZSTD-3 ratio | ZSTD-9 ratio | XZ-3 ratio | Which codec achieved fewest bytes |
|---|---:|---:|---:|---:|---|
| `repetitive.txt` | 92,160 | ~0.001 | ~0.001 | ~0.002 | ZSTD in this fixture |
| `near-duplicate.bin` | 92,160 | ~0.001 | ~0.001 | ~0.002 | ZSTD in this fixture |
| `sample.rs` | 62,648 | ~0.042 | ~0.038 | ~0.029 | XZ-3 in this fixture |
| `mixed.bin` | 93,536 | ~0.353 | ~0.353 | ~0.357 | ZSTD in this fixture |
| `uniform.bin` | 98,304 | ~1.000 | ~1.000 | ~1.001 | STORE in this fixture |
| `already-compressed.zip` | 455 | ~0.378 | ~0.378 | ~0.475 | ZSTD in this fixture |

The ZIP fixture is tiny and its DEFLATE payload is not the only constituent of the file. Its further compressibility is an example of why extension-based `STORE` routing would be wrong.

All figures exclude `.oha` archive overhead, manifest/index/dictionaries and any solid or deduplication effects. Startup and I/O dominate some sub-100 KiB timing figures. `xz` is an independent CLI that typically uses LZMA2 inside XZ framing, **not** an apples-to-apples 7z benchmark. SHA-256 verifies integrity only, not adversarial authenticity.

Source of detailed machine-readable measurements: [`synthetic-probe.json`](synthetic-probe.json).

## Verified here

- `python -m unittest discover -s tests -v`: **7/7 PASS**.
- Synthetic corpus generation: **6 files produced**.
- Compression/decompression probes for STORE, ZSTD levels 3 and 9, and XZ level 3: **72/72 roundtrips verified** (6 files x 4 codecs x 3 repetitions).
- Rust `cargo fmt/clippy/test/build`: **NOT RUN** because Rust toolchain was not installed in authoring environment.
- Windows/macOS native GUI builds: **NOT RUN**, platform environments absent.
- GitHub CI: **NOT RUN**, OHA repository not yet created.

M0 remains open. These results do not satisfy release or milestone exit criteria.
