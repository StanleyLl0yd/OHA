# OHA: accepted source license and unresolved third-party obligations (M0)

**Original OHA source-license decision: ACCEPTED on 2026-10-14.**
Project-owned OHA source is covered by **MPL-2.0**, with the official text in root [LICENSE](../LICENSE), per [ADR-0004](adr/0004-licensing.md) and source-file SPDX headers. MPL-2.0 allows commercial and noncommercial use without a fee under that public license. Distribution of covered code in source or executable form entails the applicable MPL source-availability and notice conditions; the project cannot impose a separate commercial-use royalty on recipients of MPL-covered code.

**Third-party binary redistribution clearance: OPEN (issue [#40](https://github.com/StanleyLl0yd/OHA/issues/40)).** Source-license issue #4 was closed by the owner after approving MPL-2.0; its unresolved binary-distribution work continues separately in #40. The root MPL license does **not** relicense proprietary platform runtimes, optional compression libraries, benchmark executables or third-party data. This page is a research/inventory aid, not approval to release binary products, a complete SBOM or a substitute for reviewing the exact upstream license documents.

## Current M0 dependency boundary

- The Rust workspace uses its own four local crates; no native codec is linked into the shipping Rust core. ZSTD/XZ/7-Zip commands are **external benchmark programs**, not redistributed in OHA preview bundles.
- The Windows x64 **unsigned, unpackaged, self-contained WinUI/.NET 10 preview** includes a vendor runtime footprint requiring file-by-file redistribution review. Current declared dependencies include `Microsoft.WindowsAppSDK` 1.8.260317003 and `Microsoft.Windows.SDK.BuildTools` 10.0.26100.7175, but a project/build package reference is **not** proof the referenced package contributes any shipped binary. Windows preview per-file SHA-256 inventories are available; PR [#34](https://github.com/StanleyLl0yd/OHA/pull/34) adds the separately generated exact resolved transitive NuGet reference list after `dotnet publish`. These inventories must be reconciled against one another and the actual license/redistribution grants.
- The macOS SwiftUI/AppKit app relies on host operating-system frameworks and packages its OHA Rust dynamic library. Ad-hoc code signing is not Apple Developer ID signing or notarization; an app build or code-sign check does not establish redistributed-component license clearance. Inventory any new packaged non-system dylibs.
- Preview packages contain OHA's MPL license, exact corresponding-source commit notice and preliminary third-party notes. These are **necessary inputs, not sufficient release compliance**.

## Optional native compression codec candidates (not linked in M0)

| Candidate | Upstream source-license research | Decision before integration or redistribution |
|---|---|---|
| `zstd` / `libzstd` | Upstream offers BSD-3-Clause **OR** GPL-2.0 licensing for its reference library | Prefer its BSD-3-Clause option; check exact vendored sources, Rust wrappers, linkage, binary notices and license texts |
| `xz` / `liblzma` | Modern core liblzma is advertised as 0BSD; surrounding XZ Utils files/tools may have other licenses | Recheck all compiled components and wrapper dependencies by pinned version before M2 |
| `lz4` / `liblz4` | Library offered as BSD-2-Clause in upstream sources | Verify exact version and wrappers plus notices before considering inclusion |
| `bzip3` | Upstream project licensed under LGPL-3.0 with potentially differently licensed components | **HOLD**: determine linkage, copyleft/relinking, distribution and app-platform compatibility before any inclusion |
| 7-Zip source tree | LGPL-2.1-or-later portions, other terms for some files, and special unRAR restrictions | **HOLD** for source integration; continue using installed 7-Zip only as an independent external baseline |

Upstream starting points (version-specific confirmation still required):

- [ZSTD LICENSE](https://github.com/facebook/zstd/blob/dev/LICENSE)
- [XZ Utils COPYING](https://github.com/tukaani-project/xz/blob/master/COPYING)
- [liblzma API licensing](https://tukaani.org/xz/liblzma-api/index.html)
- [LZ4 LICENSE](https://github.com/lz4/lz4/blob/dev/lib/LICENSE)
- [BZip3 LICENSE](https://github.com/iczelia/bzip3/blob/master/LICENSE)
- [7-Zip upstream license notice](https://github.com/ip7z/7zip/blob/main/DOC/License.txt)

## Remaining issue #40 evidence before binary release

1. Pin the actual release/preview commit, target platform/architecture, compiler/runtime versions, NuGet or other resolved dependency inventory, ZIP/bundle content hashes and binary-to-upstream component mapping.
2. Determine for every **actually bundled** third-party component the applicable versioned license, redistribution permission, required complete notice/license text, runtime/user terms, and any source or relinking duties. Review Microsoft SDK/.NET/WinRT requirements with exact terms, not a general NuGet badge or a package-name guess.
3. Include required texts and corresponding-source information in the right installable/release package; separately inspect any future codec dependencies, build scripts and bundled data.
4. Independently verify the distributed artifact matches the reviewed inventory and applicable platform signing/packaging requirements. Obtain owner acceptance and legal review where needed.

See [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md), [PREVIEW_M0.md](PREVIEW_M0.md) and [ADR-0004](adr/0004-licensing.md). **M0 and #40 remain open; #4 was closed after the source-license decision.** No copyright assignment, proprietary codec right or fee requirement can be inferred from this document.
