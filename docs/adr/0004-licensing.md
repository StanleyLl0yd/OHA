# ADR 0004 - Licensing gate

Status: Open (owner decision needed)

No repository license is selected. Public GitHub visibility is not a software redistribution license.

Before importing third-party dependencies:
- Record name, version, upstream, SPDX identifiers, static/dynamic linking model, license notices and source offer obligations.
- Confirm GPL/LGPL compatibility with the intended OHA distribution and App Store conditions where relevant.
- Do not import BZip3 by default until LGPL-3 obligations and distribution model have been reviewed.
- Keep external tooling in benchmarks separate from redistributable applications.

This is an explicit M0 blocker for distributing a final binary, but does not block internal research.
