# Preliminary real-file codec probe (2026-10-14)

This is **not** an OHA-vs-7-Zip comparison and does not demonstrate any adaptive compression advantage. The unselected files come from a Debian 13 container; raw inputs are not redistributed. The 9-file corpus is exploratory rather than statistically representative. SHA-256, source path and input size are recorded in `local-real-corpus-manifest.json`; individual three-run measurements and tool versions in `local-real-probe.json`.

Environment: Linux x86_64, kernel 6.18.44, Python 3.13.5, ZSTD CLI 1.5.7, XZ Utils 5.8.1. Single threaded `zstd -T1 -3/-9` and `xz -T1 -3`; independent CLI decoding, byte size and SHA-256 checked. File I/O and process startup are included in timing. Three sequential repetitions per file/codec (not randomized). No peak RSS or archive framing; results are not comparable across machines.

| Codec | Total original | Total encoded | Encoded/original | Sum of per-file median encode times | Sum of per-file median decode times |
|---|---:|---:|---:|---:|---:|
| STORE | 10,407,336 B | 10,407,336 B | 100.00% | 2.58 ms | 2.21 ms |
| ZSTD-3 | 10,407,336 B | 4,529,527 B | 43.52% | 77.11 ms | 30.94 ms |
| ZSTD-9 | 10,407,336 B | 4,319,479 B | 41.50% | 241.25 ms | 33.75 ms |
| XZ-3 | 10,407,336 B | 4,030,968 B | 38.73% | 1712.78 ms | 142.11 ms |

All 108 measured codec encode/decode roundtrips passed integrity checking. Notable tradeoff: on the 6.5 MB ELF library, XZ-3 encoded to 29.0% in about 1078 ms median, versus 35.4% in about 40 ms for ZSTD-3. A 292 KB JPEG yielded only ~6% byte saving with ZSTD-3, while still paying process start and CPU costs. These are exploratory measurements, **not selector training results**.

Outstanding research: independent `.7z` LZMA2 baseline, real multi-file archive overhead, randomized repetitions, diverse external datasets, peak RSS, cross-OS reproducibility, incremental backup trees and random-file extraction. Do not mark these requirements complete from this probe.

## Multi-file directory baseline: deterministic TAR + external codec

A separate `tools/baseline_tar.py` packs all nine files into a deterministic TAR, compresses/decompresses with an external codec, hashes the complete restored TAR, then independently walks every regular TAR member and checks bytes against source SHA-256. Files are never extracted to arbitrary paths. Six runs passed. Data and full per-run timings: `local-real-tar-baseline.json`.

| Baseline | TAR size | Encoded archive bytes | Median TAR build | Median codec encode | Median codec decode | Median member verification |
|---|---:|---:|---:|---:|---:|---:|
| TAR+ZSTD-3 | 10,424,320 B | 4,516,794 B | 4.922 ms | 54.271 ms | 14.761 ms | 17.053 ms |
| TAR+XZ-3 | 10,424,320 B | 4,033,928 B | 5.550 ms | 1913.207 ms | 112.394 ms | 16.362 ms |

This baseline **includes TAR framing and packing time** but not file discovery during the timed section, random-file extraction, memory peak or cold-cache controls. `.tar.xz` is not equivalent to a `.7z` solid LZMA2 archive. It is not evidence that OHA outperforms or matches either tool.
