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

The bench harness records input SHA-256, runtime environment and explicit scan/file/total byte limits, and rejects an explicitly empty codec list. Corpus discovery now **fails closed** on symlinked file/directory entries, non-regular entries, oversized files and an empty corpus instead of silently omitting inputs or reporting a no-data benchmark. Increase the CLI caps intentionally or select a separate corpus; do not describe an unannounced subset as the original dataset. This remains a trusted-input measurement tool and cannot guarantee data remains unchanged between discovery and reading.

`tools/baseline_tar.py` separately generates a deterministic TAR for a whole directory, compresses via external ZSTD or XZ and checks reconstructed TAR plus every member SHA-256 against a **frozen pre-run input manifest**, rejecting corpus mutation between scenarios. Its additional source rehash runs outside reported encode/decode timings; a trusted local corpus must still be quiescent during initial discovery/capture (no race-proof snapshot guarantee). See `research/local-real-tar-baseline.json`. It counts TAR packaging and compression but still lacks random-file retrieval, full scan cost, and memory profiling, and is **not** a 7-Zip baseline.

## Independent `.7z` LZMA2 benchmark harness (in validation)

`tools/baseline_7z.py`, described in `docs/BENCHMARK_7Z_M0.md`, uses a real 7-Zip CLI rather than claiming that TAR+XZ is equivalent to 7z. Its source manifest rejects parent traversal and symlinked path components; after each solid/non-solid scenario it rechecks the original file hashes and aborts on changes. This is a trusted-input integrity check, not an atomic snapshot or untrusted archive extractor. It measures full `.7z` creation, full SHA-256-verified restoration, selective extraction with SHA-256 verification and GNU-time process RSS when available. A separate PR CI workflow installs 7-Zip and records raw artifacts for a small repository text corpus. This is a **tool-validation smoke corpus**, not a performance holdout or OHA comparison. Issue #3 remains open for representative corpora and complete controlled analyses.

## Pinned Canterbury mirror, independent holdout probe (M0)

The `M0 Independent 7-Zip Benchmark` workflow now compares real external `7z`/LZMA2 archive operations and TAR+ZSTD/XZ baselines on 11 files from a pinned external compression research corpus. This remains a **baseline-only holdout probe**; it is not a measurement of OHA archive performance because a working `.oha` writer does not exist. Source: [Canterbury Corpus](https://corpus.canterbury.ac.nz/descriptions/), mirrored in [zlib-ng/corpora](https://github.com/zlib-ng/corpora) at immutable git SHA `fd01e05b0e8d1736e7178427297f3790402d4bf4`. The mirror differs in some byte counts from the historical original (e.g. `alice29.txt`), so its results must **not** be mixed with original Canterbury published ratios. The workflow verifies the precise filenames and sizes before measurement and records per-file SHA-256 and CLI versions in machine-readable results.

The 11-file bundle includes real text, source, HTML, a spreadsheet, black-and-white fax bytes and an executable. Three repetitions measure full `.7z` creation, SHA-256-verified full restoration and selected single-file retrieval, with Linux GNU-time RSS where available. TAR baselines are separate (not equivalent to 7-Zip) and include container construction cost. GitHub CI artifacts contain **JSON results only**, never the corpus bytes, respecting third-party copyright/redistribution ambiguity. Research results are not user-workload representative, do not include precompressed media/VM data or OHA codecs, and remain subject to #3's broader data coverage and statistical holdout requirements.

## Selected-file method change (M0)

The independent 7-Zip research harness now writes a selected archive member to disk in a clean scratch location and verifies it with streaming SHA-256. This removes the previous 1 MiB in-memory stdout restriction and supports large files such as database/VM benchmarks. Each repetition selects a deterministic target shared by solid on/off modes. Older selective-latency measurements used stdout and **are not directly comparable** to the new disk-output series. The method/seed and selected-file byte count are recorded in raw JSON. The benchmark remains external 7-Zip only, not an OHA format result.

## Reproducible descriptive dispersion summaries (M0)

`tools/summarize_baseline.py` consumes only the raw **independently SHA-256-verified** 7z and TAR baseline reports, never a guessed OHA archive measurement. The independent workflow now publishes one extra `*-summary.json` per existing raw report (repository docs, pinned historical Canterbury mirror and owned synthetic mixed corpus, both archive types separately). The summary groups 7z by solid/non-solid and TAR by external codec; each scenario must have exactly the declared repetitions with no duplicate/missing run or unverified integrity. For each measured metric it reports median, minimum, maximum and median absolute deviation (MAD). Unavailable RSS remains JSON `null`, never `0`; mixed measured/missing RSS is rejected. TAR build+compression timing is reported explicitly as a sum. **Selected-file extraction timings are not pooled**, because different files can be selected in different repetitions.

These statistics quantify variation **within only 2-3 uncontrolled CI repetitions**; they are not confidence intervals, speed rankings, a cold-cache study or evidence that OHA beats any reference tool. Full #3 acceptance still requires legitimate representative held-out corpora, realistic controlled warm/cold cache, sufficient repetitions, independent decoder resource use and real OHA product-level measurements after M1.
