# M0 rights-clean mixed synthetic benchmark workload

Status: research-only corpus generator, **NOT representative actual user archives, VM data, photos, videos or customer databases**.

The generator at `tools/make_mixed_corpus.py` uses only Python's standard library and deterministic, project-authored source data. It produces 136 reproducible files: structured text, high-entropy pseudo-random bytes, an 8 MiB sparse disk-like byte image, two nearly identical snapshots with small controlled changes, a generated SQLite database, already-compressed ZIP and GZIP inputs, and 128 small JSON records.

All data is generated transiently in GitHub Actions and contains no personal/customer content or third-party copyrighted corpus bytes. The JSON manifest records SHA-256, category, byte count, seed, SQLite runtime version and exact filenames. The actual corpus files are not uploaded as build artifacts.

The independent benchmark workflow runs real 7-Zip LZMA2 solid/non-solid and TAR+XZ/ZSTD on the generated directory, verifies full-restoration SHA-256 integrity and uploads only raw machine-readable benchmark JSON plus the corpus manifest.

This expands **coverage of the benchmark harness**, not evidence of OHA compression advantage. Fake VM-like data is not an actual VM image. SQLite is an artificial database and does not represent application-specific DB workloads. The data generator is not tuned using adaptive OHA results; there is no working OHA writer yet. Timing from shared CI runners uses uncontrolled caches and should not be presented as hardware-neutral or as a modern real-world representative holdout.

Before completing issue #3, separately test permission-cleared real modern mixed corpora, cold/warm cache controls, median+dispersion, decoder RSS, selective extraction and full archive overhead. Owner input may be required to provide lawful representative data; no private data should be placed in public GitHub artifacts.

License: the original generator source is MPL-2.0. Generated artificial corpus contents are not based on external copyrighted datasets. Benchmark binaries ZSTD/XZ/7-Zip remain external tools under their own licenses and are not redistributed by OHA.
