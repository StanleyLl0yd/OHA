# M0 current status and handoff

Updated 2026-10-14 after resumed M0 research.

## Complete in local scaffold

- Brand, platform contract, CLI naming and `.oha` extension recorded.
- Architecture/ADR baseline, draft format requirements, threat model, selection policy and milestone plan.
- Bounded std-only Rust byte sampler plus deterministic candidate ranking library; CLI experimental `analyze` command. Rust source has not been compiled in the authoring environment.
- Python codec-probe harness hardened with scan/corpus size bounds, SHA-256 source metadata; 28 Python unit tests now pass.
- Re-ran and verified 72 synthetic codec roundtrips; also verified 108 individual real-file codec roundtrips and six TAR+ZSTD/XZ directory archive roundtrips. Local result JSON, per-file provenance and methodology recorded.
- `.github/workflows/ci.yml` prepared with explicit OS runner labels; Rust 1.89.0 pinned in rust-toolchain.toml. CI not executed on GitHub.
- Added candidate v1 wire offsets and read-only CRC32C header/footer probe with negative tests. Spec unapproved and no actual writer/reader exists.
- Recorded upstream candidate codec licensing findings; application license undecided.
- `AGENTS.md` audit protocol and mandatory two-pass repository-wide exit audit after each milestone.

## Actual blockers

1. Target GitHub repo `StanleyLl0yd/OHA` does not exist; connected GitHub tool does not support repository creation. No remote changes were made.
2. No Cargo/rustc available locally (network/DNS unavailable): Rust fmt, Clippy, test, build not verified.
3. No Windows/macOS runners available here: no native GUI prototypes or binding tests.
4. No project LICENSE chosen; public binary distribution compliance pending.
5. `.oha` byte format intentionally not stabilized or implemented; data migration/versioning requires approval.

## Next concrete actions

1. Create repository `StanleyLl0yd/OHA` and import this scaffold, ideally using a short-lived PR branch.
2. Generate `Cargo.lock`, run format/clippy/tests on Rust 1.89 and resolve any failures; pin CI runner images/toolchain as appropriate.
3. Expand exploratory real-file and TAR+codec results to representative licensed holdout datasets, full 7-Zip baseline, peak RSS and random extraction (not completed).
4. Decide application LICENSE and exact third-party version/license/linking/packaging obligations; candidate upstream research is recorded.
5. Review the new unapproved wire v1 framing proposal, complete canonical manifest/index and codec registry, then create genuinely independent conformance vectors before approving the spec.
6. Create WinUI and SwiftUI/AppKit minimal buildable shells, prototype Rust FFI ownership, progress, cancellation and errors; test each on real OS.
7. Perform final M0 two-pass repo-wide review/verification and attach evidence; only then close M0.
