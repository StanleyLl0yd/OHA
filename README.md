# OHA - Optimized Hybrid Archiver

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

Requires Rust 1.89.0 or newer compatible with edition 2024. The following Rust commands have **not** been executed by the creator of this scaffold because Cargo was unavailable in the authoring environment.

```sh
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo run --bin oha-archiver -- analyze path/to/file
```

Python 3.10+ is sufficient for the research harness; for compression benchmarks, installed external `zstd` and `xz` binaries are detected automatically. No Python packages are required.

```sh
python3 -m unittest discover -s tests -v
python3 tools/make_corpus.py --output ./sample-corpus
python3 tools/benchmark.py ./sample-corpus --output ./bench-results.json --repetitions 3
```

**Do not use synthetic corpus results to claim superiority over other archivers.** Real-world corpora, baseline 7-Zip, random extraction, RAM measurements, cold/warm cache repetitions and cross-platform compatibility tests are required before performance statements.

## Important decisions that remain open

- Public-source license: **not chosen**. Do not assume an open-source license is granted by this distribution or add one without owner approval.
- `.oha` binary wire specification: **draft constraints only**. No backwards-compatibility promises yet.
- Codec dependencies: STORE + ZSTD first; LZMA2, BZip3 and LZ4 only after legal and cross-platform assessment.
- BLAKE3 and FastCDC for M3, after M1/M2 reliability requirements are satisfied.
- Security/crypto design: no home-grown cryptography; authenticated encryption added after threat model review.
- Windows/macOS GUI prototypes: design fixed, executable GUI scaffolds not yet created or tested.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for acceptance criteria and unresolved work.

## M0 updates on 2026-10-14

- Exploratory local real-file measurements: `docs/research/REAL_PROBE_RESULTS.md` (no OHA vs 7-Zip claim).
- **Unapproved** candidate binary framing: `docs/FORMAT_V1_PROPOSAL.md` and read-only `tools/wire_header_probe.py`. This is not a working `.oha` implementation.
- Candidate dependency licensing research: `docs/LICENSING_RESEARCH.md`. No distribution LICENSE selected.
- Toolchain pin: `rust-toolchain.toml` (1.89.0); Cargo cannot be built in the current authoring environment and requires CI verification.
