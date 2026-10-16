# GitHub repository bootstrap (completed 2026-10-14)

Repository: https://github.com/StanleyLl0yd/OHA (public).

- Default branch: `main`.
- Initial bootstrap commit: `3c20abde5b4ae7d6cbe5992ce1f805dd4f517746`.
- Research scaffold imported as draft PR #1: https://github.com/StanleyLl0yd/OHA/pull/1.
- 44 original scaffold files plus subsequent CI fixes, lockfile and documentation.
- Six focused M0 issues: #2 through #7.

The imported `.oha` binary framing is an unapproved proposal, not an implemented archival format. At the *initial bootstrap snapshot* the repository did not yet have an approved source license; **later on 2026-10-14 the owner approved MPL-2.0**, now committed as root `LICENSE` and recorded in ADR-0004. Repository visibility alone would not have granted permission to use the source before the license decision.

Before completing M0, ensure **separate third-party binary redistribution clearance** (the project source license is already approved), defensible benchmarking, physical GUI acceptance in addition to native CI builds, owner-reviewed wire format and mandatory two-pass complete-repository audit. See `docs/ROADMAP.md` and `AGENTS.md`.

Protect `main` after the CI job names stabilize. Never bypass failing checks merely to merge.
