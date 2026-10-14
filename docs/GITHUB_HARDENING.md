# GitHub hardening (M0)

Reference configuration: `StanleyLl0yd/password-generator` as inspected on 2026-10-14.

- All workflow Actions pinned by full commit SHA; containers pinned by digest; top-level workflow token permissions `{}` and scoped per-job access.
- CI `verify` aggregation fails closed on Rust (Linux x64, Windows x64, macOS ARM64/Intel), Python, Semgrep, Gitleaks and PR dependency review.
- CodeQL `security-extended` scans Rust, Python and GitHub Actions source. Code scanning is a separate workflow rather than a custom test-substitute.
- Cargo lockfile checked with `--locked`; Dependabot proposes Cargo and GitHub Action updates; secret scanners check changes and Git history.
- Repository-side controls (admin-only) are applied with the associated `pwsh + gh` bootstrap: PR-only default branch, strict required `verify` check, signed commits, CodeQL merge gate, no deletion/force-push, immutable `v*` release tags, least-privilege Actions token, and merge settings.
- No third-party PR code is executed through `pull_request_target`; no long-lived credentials are persisted by checkout.
- A code scanning gate must only be made active once CodeQL has produced a successful baseline on `main`.
- This is repository hardening, not the final M0 repository-wide security/code audit. Packaging/signing and native FFI verification remain separate M0 gates.
