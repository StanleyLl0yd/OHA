# M0 independent 7-Zip archive benchmark

`tools/baseline_7z.py` is a standalone research baseline. It uses a **real external 7-Zip executable** to create LZMA2 `.7z` archives, fully extract each archive to a fresh scratch directory and verify every regular file by size and SHA-256. It then extracts one deterministically selected file to a separate temporary directory and verifies that file by streaming SHA-256. Unlike the earlier stdout-based probe, selected files can be large, bounded by the normal source file and corpus limits. No OHA `.oha` encoder exists, so this is **not** an OHA performance result.

## Reproducible run

```sh
python3 tools/baseline_7z.py path/to/your/corpus --output /tmp/oha-7z-baseline.json --repetitions 3
python3 tools/baseline_tar.py path/to/your/corpus --output /tmp/oha-tar-baseline.json --repetitions 3
```

The `M0 Independent 7-Zip Benchmark` GitHub Action installs 7-Zip on Ubuntu, executes a tiny real repository-owned documentation corpus, and uploads both machine-readable results as an artifact. This **smoke corpus** is source-controlled and reproducible but highly text-biased, small, and *not* an independent representative holdout. Do not extrapolate its numbers to VM images, video, databases or diverse file trees.

## Interpretation and safeguards

- Versions, OS, architecture, fixed `-mx=5`, single-thread LZMA2, source file hashes, and shuffled solid/on-off order are recorded.
- Encode time covers full `.7z` archive creation and metadata. Full extraction and selected-file extraction are separately timed. Output checksums cover every input file.
- Selected-file extraction uses a fresh temporary directory and streaming SHA-256 rather than collecting stdout in memory; any corpus file within the existing CLI per-file cap can be selected. One deterministic target per repetition is shared between solid on/off for fairness. No 1 MiB restriction remains.
- **Metric break:** selective extraction latency from PR #25 onward measures *disk output*, whereas older JSON used stdout-to-memory. Never combine the two selective latency series as identical methods. Encoder/full-extraction timings are measured as before.
- GNU `/usr/bin/time -f %M` peak RSS is reported per child process on Linux when available, otherwise RSS is `null` (not invented).
- Measurements use uncontrolled filesystem caching, temporary storage and GH-hosted runner performance; they are not controlled hardware trials. Warm/cold cache normalization and statistical power remain future work.
- The benchmark rejects symlink roots and discovered symlink inputs, line-break-containing filenames (7-Zip list-file constraint), unexpected extracted entries, content corruption, missing files, and invalid input bounds. This is a **trusted-input benchmark only**, not a safe general-purpose extractor for malicious archives.
- The original `tools/baseline_tar.py` checks TAR+ZSTD/XZ independently. Its times and 7-Zip times should be compared only on the **same corpus and machine** with clearly declared differences in packaging, codec flags and solid settings.

Issue #3 stays open pending broader rights-reviewed corpora, repetition/dispersion analysis, holdouts, balanced mixed-content data, and explicit evaluation against a future implemented OHA archive policy.
