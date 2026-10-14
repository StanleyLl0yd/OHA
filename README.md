# OHA - Optimized Hybrid Archiver

**License:** [Mozilla Public License Version 2.0 (MPL-2.0)](LICENSE). Both commercial and noncommercial uses are permitted under MPL-2.0, with its source and notice obligations.

**Status:** M0 architecture / research. **This is not yet a usable archiver.**

OHA is an offline, cross-platform hybrid data archiver designed to choose suitable lossless codecs, grouping, dictionaries and deduplication strategies for individual datasets while respecting compression time, decompression time and memory budgets.

## Fixed product decisions

| Component | Decision |
|---|---|
| Name and format | OHA / `.oha` |
| Shared core | Rust |
| Windows | Native WinUI 3 + C# UI, plus Rust CLI |
| macOS | Native SwiftUI + AppKit UI, plus Rust CLI |
| Linux | Rust CLI initially; Linux GUI deferred |
| CLI command | `oha-archiver` to avoid existing `oha` HTTP benchmarking tool |
| Deployment | Fully offline: no backend, no account, no telemetry by default |
| Versioning | Numeric versions only; no alpha/beta/rc suffixes |
| Format stability | No frozen wire specification or production `.oha` writer at M0 |

The repository includes an early, dependency-free Rust analysis and codec-selection **research prototype**, a reproducible compression comparison harness, technical designs and security requirements. `oha-archiver analyze PATH` is an experimental analysis command; pack/extract are not implemented.

## Repository layout

```text
apps/oha-cli/                  Experimental Rust CLI
crates/oha-analysis/           Bounded byte-level sampling and metrics
crates/oha-policy/             Testable selection policy and budgets
crates/oha-ffi/                Experimental bounded C ABI analysis probe
apps/oha-windows/              Native WinUI 3/C# prototype (Windows x64)
apps/oha-macos/                Native SwiftUI/AppKit prototype (macOS)
apps/oha-windows-ffi-smoke/    C# -> Rust PInvoke smoke
docs/adr/                      Architecture decisions
docs/ARCHITECTURE.md           Components, platform boundaries
docs/FORMAT_DRAFT.md           Not-yet-frozen .oha format requirements
docs/DECISION_ENGINE.md        Decision optimization and evaluation
docs/SECURITY.md               Threat model and extraction constraints
docs/ROADMAP.md                Milestones and exit criteria
docs/RESEARCH.md               Alternatives, dependencies, licenses
docs/BENCHMARKS.md             Measurement methodology
tools/benchmark.py             Real codec measurements through local CLI tools
tools/make_corpus.py           Deterministic synthetic smoke corpus
tests/test_benchmark.py        Research harness regression tests
```

## Running the research scaffold

Requires Rust 1.89.0 or newer compatible with edition 2024. Rust workspace formatting, Clippy, unit tests and build PASS on GitHub Actions with Rust 1.89.0 for Linux x64, Windows x64, macOS ARM64 and macOS Intel. Native C#/Swift FFI smoke is also required by protected CI.

```sh
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --locked -- -D warnings
cargo test --workspace --locked
cargo run --bin oha-archiver -- analyze path/to/file
```

Python 3.10+ is sufficient for the research harness; for compression benchmarks, installed external `zstd` and `xz` binaries are detected automatically. No Python packages are required.

```sh
python3 -m unittest discover -s tests -v
python3 tools/make_corpus.py --output ./sample-corpus
python3 tools/benchmark.py ./sample-corpus --output ./bench-results.json --repetitions 3
```

**Do not use synthetic corpus results to claim superiority over other archivers.** An independent real 7-Zip LZMA2 research baseline is present; representative holdout corpora, controlled RSS and cold/warm repetitions, and an actual OHA writer are still required before performance claims.

## Remaining design and release gates

- OHA's original source code is licensed under **MPL-2.0**, with file-level copyleft and attribution/notice requirements when distributing covered modifications; third-party library licenses remain separate.
- `.oha` binary wire specification: **draft constraints only**. No backwards-compatibility promises yet.
- Codec dependencies: STORE + ZSTD first; LZMA2, BZip3 and LZ4 only after legal and cross-platform assessment.
- BLAKE3 and FastCDC for M3, after M1/M2 reliability requirements are satisfied.
- Security/crypto design: no home-grown cryptography; authenticated encryption added after threat model review.
- Windows/macOS GUI: native shells compile in CI and call the Rust experimental ABI; unsigned/ad-hoc research preview bundles are built and inventoried, but interactive device UX, production packaging/signing and long-running jobs are not verified.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for acceptance criteria and unresolved work.

## M0 updates on 2026-10-14

- Exploratory local real-file measurements: `docs/research/REAL_PROBE_RESULTS.md` (no OHA vs 7-Zip claim).
- **Unapproved** candidate binary framing: `docs/FORMAT_V1_PROPOSAL.md` and read-only `tools/wire_header_probe.py`. This is not a working `.oha` implementation.
- OHA project source license is MPL-2.0, governed by root `LICENSE`. Details: `CONTRIBUTING.md`, `AUTHORS.md`, `THIRD_PARTY_NOTICES.md` and `docs/LICENSING_RESEARCH.md`.
- Toolchain pin: `rust-toolchain.toml` (1.89.0); the complete Rust workspace builds and tests on four hosted CI configurations.

## Native and security verification

The GitHub `verify` check is a fail-closed merge gate for Rust/Python tests, Semgrep, Gitleaks, Dependency Review (on PRs) and native WinUI/SwiftUI builds plus cross-language smoke tests. CodeQL scans Rust, Python, Actions, C# and Swift separately. `.oha` serialization and archive extraction are still unimplemented, and M0 exit requires the complete documented audit.

- Proposed `.oha` DATA/MNFT/INDX 80-byte frame-header research validations were added by PR #13; the format is unapproved and no archive writer or decoder exists.

## License, authors and binary recipients

Original OHA source is released under [Mozilla Public License 2.0](LICENSE). Initial project maintainer: [StanleyLl0yd](https://github.com/StanleyLl0yd), with contributors credited in Git history. Copyright and license notices must be preserved. Distributing modified MPL-covered code requires making the corresponding covered source available under MPL-2.0. Private, including internal commercial use, need not publish modifications. A fee is **not** required for commercial use under MPL.

Source availability: https://github.com/StanleyLl0yd/OHA. Third-party runtimes, native codec libraries, bundled binary dependencies and benchmark data are **not relicensed** by OHA's MPL. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [docs/PREVIEW_M0.md](docs/PREVIEW_M0.md). Previews remain research-only and do not indicate completed redistribution clearance.
