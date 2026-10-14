# ADR 0004 - OHA licensing decision gate

Status: **PROPOSED (NOT ACCEPTED)**, 2026-10-14.

## Context

Public GitHub visibility does not grant source redistribution rights. OHA needs a deliberate project-source license plus an independent third-party software redistribution policy. Current Rust code is internally dependency-free; self-contained WinUI packaging includes Microsoft runtime components.

## Preferred direction, subject to owner approval

License original OHA Rust/C#/Swift/C source under **MIT OR Apache-2.0**, chosen by each recipient. This enables external reuse and paid/commercial products and provides Apache patent terms; it does not mandate publication of forks. The owner must choose whether permissive licensing or MPL-2.0 file-level copyleft better serves project goals, and confirm accurate copyright attribution.

## Proposed codec/packaging rules

- Prefer reviewed permissive codec libraries: libzstd (BSD-3-Clause), liblzma (0BSD), liblz4 (BSD-2-Clause); exact linked version and notices must be confirmed.
- Defer LGPL-3.0 BZip3 and 7-Zip source imports until reviewed; 7z benchmark binary is external only.
- Separate original OHA source license from native Microsoft/Apple platform components and other third parties.
- Require release inventory, bundled notices, transitive NuGet/Cargo license audit and actual Windows App SDK redistribution/acceptance assessment.
- M0 previews are research probes, not evidence of commercial distribution clearance.

## Action after acceptance

Add authoritative license texts, Cargo SPDX metadata, contribution and third-party notices, then validate in protected CI. Until owner approval, no LICENSE files are added, and issue #4 remains OPEN.

More evidence and original upstream links: docs/LICENSING_RESEARCH.md.
