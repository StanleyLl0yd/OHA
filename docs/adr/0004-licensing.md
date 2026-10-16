# ADR 0004 - Project source license

Status: **ACCEPTED**, 2026-10-14 (owner decision)

Original, project-owned OHA source code is released under the **Mozilla Public License Version 2.0 (MPL-2.0)**. Its complete unmodified canonical text is in root `LICENSE`. Code uses `SPDX-License-Identifier: MPL-2.0`; Cargo manifests carry the same SPDX license ID.

- Personal, academic and commercial use is royalty-free, including forks and integrations. No paid commercial license is required under MPL-2.0.
- When distributing modified covered source files or executable forms, comply with Sections 3.1-3.4: covered modifications remain MPL-2.0 and corresponding source must be obtainable by recipients, while separate additions in a Larger Work can have different terms.
- Private/internal modifications need not be published. Preserve copyright notices and attribution/history; this license does not demand homepage credit beyond its notices.
- OHA does not add Exhibit B incompatibility language. No contributor copyright assignment or CLA is imposed. Any later proprietary relicensing of outside contributions would require sufficient independent rights.
- Copyright ownership follows actual contributors; project maintainer `StanleyLl0yd` is credited without making unsupported claims about third-party ownership.

**Separate release gate:** neither MPL nor the root LICENSE grants permissions to redistribute Microsoft Windows App SDK/.NET, Apple software, optional codec libraries, external benchmark sources or corpora. Exact-version binary inventory, third-party notices, platform SDK terms and release approval are still required; issue #40 tracks the open third-party redistribution clearance; the owner closed the original source-license issue #4.
