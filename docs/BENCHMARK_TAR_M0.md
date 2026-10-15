# M0 TAR compression baseline reproducibility

The independent `tools/baseline_tar.py` measures TAR package construction plus external ZSTD-3 and XZ-3 compression/decompression on trusted, preselected source files. The restored TAR bytes and every contained regular file are independently SHA-256 verified. This is **not** a `.7z` result and is **not** an OHA archive performance result.

Starting with this benchmark revision, each raw JSON result includes host platform, CPU architecture, Python version, the **actual external codec version banners**, deterministic run ordering seed (`271828`), order position, repetitions and an explicit uncontrolled/warm-variable filesystem-cache note.

Codec/repetition combinations are shuffled by a fixed seed rather than always executing ZSTD then XZ. The order is reproducible across machines running the same code, but elapsed time, memory, IO and thermal behavior are not. TAR creation remains counted separately; end-to-end encode time is `tar_build_ms + encode_ms`.

Selective member retrieval and peak RSS are not measured by this TAR comparator; those are separate 7-Zip baseline metrics. The PR #25 7-Zip selected-file mode changed from stdout to disk output, so cross-revision selected-extraction latencies must not be mixed. Neither benchmark determines how OHA would perform before M1 implements a real `.oha` writer.

Benchmark corpus licenses and distribution permissions remain independent: historical public Canterbury/Silesia sources must not be vendored without rights. Issue #3 remains OPEN for independent modern mixed workloads, repeat dispersion, controlled cold/warm cache and complete codec/metadata overhead comparisons.
