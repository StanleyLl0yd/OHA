# M0 Windows preview: independently verified modular WinUI artifact delta

**2026-10-16. Technical research evidence only. NOT a release, complete SBOM, third-party license clearance, endorsement of distribution, or physical device/GUI acceptance.** Resolves no open M0 gate by itself. See [#40](https://github.com/StanleyLl0yd/OHA/issues/40), [#16](https://github.com/StanleyLl0yd/OHA/issues/16), and [#6](https://github.com/StanleyLl0yd/OHA/issues/6).

## Exact independent artifact evidence

| Property | Before modular WinUI (historical) | After modular WinUI (post-merge main) |
|---|---|---|
| Source commit | `1ec9e0b7c988611c55268a180e91807f7f957058` | `22d1e7bed90b6f20c5d4b3f534a1ae87f74162da` |
| GitHub Actions run | [38883058987](https://github.com/StanleyLl0yd/OHA/actions/runs/38883058987) | [38901255888](https://github.com/StanleyLl0yd/OHA/actions/runs/38901255888) |
| Windows artifact ID | `12038490977` | `12045957048` |
| Downloaded outer ZIP SHA-256 | `b21a3288730e2c39c43a630cb3ed4ceb3d90815bd332d2ea6827013fd1664d17` | `ac24c31b03b5d6ce3087704b30ee603a5d5ec82c09b589825127db7247ad67d3` |
| Nested Windows package regular files | 512 | 455 |
| Sum of nested regular-file bytes (including SHA256SUMS) | 224,337,584 | 172,199,900 |
| Independent SHA256SUMS matches (manifest excluded) | 511/511 | 454/454 |
| Heuristic binary candidates, not individual license findings | 319 | 269 |
| Candidates not matching any `.deps.json` runtime/native/resources **basename** | 94 | 54 |
| Exact resolved NuGet package IDs (build + runtime, not all distributed) | 14 | 7 |

The after-artifact reduces the *uncompressed contents* by **52,137,684 bytes (23.241%)**, with **57 fewer regular files**. Among the prior nested paths, **443** have exactly the same SHA-256; 57 disappeared and 11 surviving paths have different hashes (application binaries/manifests, Rust library and several metadata/runtime components). No new nested regular-file paths appeared. Archive ZIP size is a different metric and must not be substituted for unpacked-file bytes.

Both complete outer ZIPs were independently SHA-256 checked against GitHub's artifact digests. Every nested regular file listed in each `SHA256SUMS.txt` was hashed directly from ZIP entries in memory; path names and manifest completeness were checked, not extracted to arbitrary filesystem destinations. The sidecar Windows inventories and resolved NuGet JSON were read from the **same respective artifacts**. A successful hosted build and intact ZIP still do not prove end-user runtime/GUI behavior, publisher identity, or redistribution rights.

The new source is merged [PR #45](https://github.com/StanleyLl0yd/OHA/pull/45), which replaced the Windows App SDK umbrella package with the exact `Microsoft.WindowsAppSDK.WinUI 1.8.260224000` plus required standalone build tooling. The package reference and build-level exclusion check caused unnecessary AI/ML native dependencies to disappear **without post-publication manual DLL removal**. The resolved new package IDs are `Microsoft.Web.WebView2`, `Microsoft.Windows.SDK.BuildTools`, `Microsoft.Windows.SDK.BuildTools.MSIX`, `Microsoft.WindowsAppSDK.Base`, `Microsoft.WindowsAppSDK.Foundation`, `Microsoft.WindowsAppSDK.InteractiveExperiences`, and `Microsoft.WindowsAppSDK.WinUI`. Build tools are not automatically shipped binary components.

Notably absent from the new nested package: `DirectML.dll`, `onnxruntime.dll`, `onnxruntime_providers_shared.dll`, and `Microsoft.Windows.AI.MachineLearning.dll`. WinUI still ships substantial Windows/.NET runtime and UI files. The **54 basename-unmatched candidates** are not proven third-party licensing violations, but neither are they cleared: `.deps.json` is incomplete for native attribution and basename equality does not prove package provenance.

## Version-specific legal blockers

The [official Microsoft Windows App SDK WinUI 1.8.260224000 license](https://www.nuget.org/packages/Microsoft.WindowsAppSDK.WinUI/1.8.260224000/License) is titled **Microsoft Software License Terms / Microsoft Windows App SDK**, rather than Engineering Preview. Section 3 specifies conditional redistribution rights, **significant primary functionality**, sufficiently protective terms for distributors/external end users, developer indemnification, and restrictions on misrepresenting Microsoft endorsement or changing terms of Microsoft code. The separate .NET Windows runtime/component licensing and full component notices also need review. Neither the app's MPL-2.0 source LICENSE nor CI passing satisfies these obligations.

The current M0 preview is only a native Rust analysis demo, *not a working archiver*. It must not be declared to meet the significant-primary-functionality condition without accountable review. Preserve full versioned license/EULA texts and per-file upstream attribution, match remaining files to exact NuGet payload hashes or other reliable origins, record legal/owner decision, and retest the eventual release-specific package.

## Remaining gates

- **#40 OPEN:** 54 still unmatched-by-basename heuristic binary candidates; obtain exact-version binary ownership/license/notice texts and Microsoft end-user terms. An inventory is not a software bill of materials or legal signoff.
- **#16 / #6 OPEN:** physical Windows x64 and macOS GUI launch, FFI output, missing-native-DLL negative test, clean exit and platform policies still require owner-run observations tied to an exact artifact. Windows EXE remains unsigned; macOS uses ad-hoc signing, not notarization.
- **#3/#5/#7/M0 OPEN:** benchmark representativeness, explicitly accepted wire contract and mandatory two full repository-wide exit audit passes remain unresolved. No M1 implementation is authorized.

These artifact IDs have limited Actions retention; preserve the exact source hashes/run IDs above. A future release or different runtime publish must regenerate **all** file hashes and license analysis. No binary payloads are committed here.
