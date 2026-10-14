# Compression benchmarking protocol

## Primary question

Does constrained, content-aware selection of codecs and grouping provide a repeatable archive size/latency/decoder-memory advantage over simple fixed codecs on unseen heterogeneous datasets?

## Method

- Freeze corpus selection before selector tuning: source code, JSON/logs, office docs, images/media, executables, VMs, databases, incompressible bytes, tiny file trees, versioned snapshots. Include public or user-owned redistributable data with provenance/rights.
- Use hardware specs, OS and versions, filesystem, cold/warm cache policy, storage medium, external codec exact version and command flags in every report.
- `STORE`, ZSTD (specific declared levels), 7-Zip LZMA2 with documented level/dictionary/solid flags, independent LZMA2/XZ (not equivalent to `.7z`), and proposed OHA policies.
- Count end-to-end time, including scan, samples, dictionary training, grouping, checksums, index and disk write. Measure decompression separately, both full and random-file extraction. Measure peak working-set RSS and disk I/O where supported.
- Verify every compressed output by *full* decompression and matching hash before accepting a data point; independent decode, not just exit code.
- Run multiple reps in randomized order; report median and dispersion, not only the fastest run. Note system thermal frequency and memory page cache effects.
- Report all incompressible and negative cases, including OHA regressions. Avoid tuning on evaluation holdout data.
- Store machine-readable CSV/JSON with exact reproducible commands, then generate charts separately.

## Scope of bundled Python research harness

The included `tools/benchmark.py` is a **lightweight compression probe**, not a full archive benchmark: it tests individual files with `zstd` and `xz` when installed, and STORE; process spawn and I/O are included; peak RSS not measured; output in each case is verified by independent decoder command. It is useful to prove harness correctness and gather initial intuition, **not** to claim product performance or a fair 7z comparison.

`tools/make_corpus.py` creates deterministic artificial data exclusively for tests; it is not a representative workload benchmark.

## 2026-10-14 exploratory measurements

Nine real locally installed file samples measured with STORE, ZSTD-3, ZSTD-9 and XZ-3 (three reps each, 108 verified roundtrips). See `research/REAL_PROBE_RESULTS.md`, `research/local-real-corpus-manifest.json` and `research/local-real-probe.json`. These are preliminary codec probes, **not** archive end-to-end or representative holdout measurements.

The bench harness now records input SHA-256, runtime environment and explicit scan/file/total byte limits, and rejects an explicitly empty codec list. The script does not follow input symlinks while discovering corpus files.

`tools/baseline_tar.py` separately generates a deterministic TAR for a whole directory, compresses via external ZSTD or XZ and checks reconstructed TAR plus every member SHA-256. See `research/local-real-tar-baseline.json`. It counts TAR packaging and compression but still lacks random-file retrieval, full scan cost, and memory profiling, and is **not** a 7-Zip baseline.
