# M0 native preview: independent artifact-integrity evidence (2026-10-16)

**Research inventory only, not a release, third-party redistribution approval, notarization, Authenticode signing, physical GUI acceptance or a complete SBOM.** Tracks [#16](https://github.com/StanleyLl0yd/OHA/issues/16), [#6](https://github.com/StanleyLl0yd/OHA/issues/6) and the open binary licensing gate [#40](https://github.com/StanleyLl0yd/OHA/issues/40).

## Exact evidence source

- Repository: `StanleyLl0yd/OHA`; source commit: `1ec9e0b7c988611c55268a180e91807f7f957058`.
- Successful hosted [M0 Native Preview Artifacts run 38883058987](https://github.com/StanleyLl0yd/OHA/actions/runs/38883058987). Runner-local packaging/signature checks are distinct from the independent artifact-byte checks below.
- Artifact ZIPs were retrieved from GitHub Actions for **that one run**. SHA-256 was computed on each outer artifact ZIP and compared with GitHub's `digest`. Each nested bundle was inspected as ZIP bytes, without executing binaries or unpacking untrusted paths to the filesystem.
- SHA-256 of *every packaged regular file* was independently recalculated from the nested ZIP and matched against the artifact's `SHA256SUMS.txt` and machine-generated inventory JSON. Path traversal, absolute paths and symlink entry types were screened. No mismatches were found.
- Hosted previews are temporary (7-day artifact retention, approximately until 2026-10-23 UTC). Keep exact run/SHA in any later physical acceptance record; a rebuilt preview has different provenance.

| Target | Actions artifact ID | Outer ZIP SHA-256 | Manifest / packaged regular files | Packed regular-file bytes | Independent hash/path audit |
|---|---:|---|---:|---:|---|
| Windows x64 | `12038490977` | `b21a3288730e2c39c43a630cb3ed4ceb3d90815bd332d2ea6827013fd1664d17` | 511 hashes / 512 files (excluding the manifest itself) | 224,337,584 | PASS |
| macOS ARM64 (`macos-15`) | `12037669983` | `0af0818bae8ac3a13776e9412bf81c453515e427e20a593dacc91e97cd403271` | 7 hashes / 7 files | 576,778 | PASS |
| macOS Intel (`macos-15-intel`) | `12037534611` | `4e891af42d3bd67d997351d345e67e06389450dca99a896e2f63d5d562aaa3de` | 7 hashes / 7 files | 541,370 | PASS |

macOS bundles include `Contents/_CodeSignature/CodeResources`, `Contents/Info.plist`, OHA's executable and Rust dylib, `LICENSE`, `SOURCE-CODE.txt` and preliminary `THIRD_PARTY_NOTICES.md`. Both external complete file-checksum manifests match exactly. **This independently checks bytes, not the validity of an Apple Developer ID identity, notarization or device Gatekeeper behavior.** Hosted workflow also ran `codesign --verify --deep --strict` on the unpacked app; that is not physical-owner acceptance.

## Windows redistribution inventory: technical facts only

The Windows ZIP's `OHA-M0-Windows-x64-inventory.json` reports **512 regular files**, 224,337,584 total bytes, including **272 DLLs, 172 .mui resources, 46 .winmd metadata files** and other resources. Its heuristic `third_party_binary_candidates_unreviewed` list contains **319 paths**. These are candidates for per-binary attribution, not 319 distinct licenses or licensors. Embedded `OHA.Windows.deps.json` is available for further mapping. The package contains OHA's own `LICENSE`, `SOURCE-CODE.txt` and **preliminary, explicitly non-clearing** `THIRD_PARTY_NOTICES.md`.

The sibling `OHA-M0-Windows-x64-nuget.json` reports the following **resolved references**, not a demonstrated one-to-one file mapping:

| Package | Exact resolved version | Reference |
|---|---|---|
| Microsoft.WindowsAppSDK | 1.8.260317003 | Direct |
| Microsoft.Windows.SDK.BuildTools | 10.0.26100.7175 | Direct |
| Microsoft.Web.WebView2 | 1.0.3179.45 | Transitive |
| Microsoft.Windows.SDK.BuildTools.MSIX | 1.7.20250829.1 | Transitive |
| Microsoft.WindowsAppSDK.AI | 1.8.53 | Transitive |
| Microsoft.WindowsAppSDK.Base | 1.8.251216001 | Transitive |
| Microsoft.WindowsAppSDK.DWrite | 1.8.25122902 | Transitive |
| Microsoft.WindowsAppSDK.Foundation | 1.8.260222000 | Transitive |
| Microsoft.WindowsAppSDK.InteractiveExperiences | 1.8.260125001 | Transitive |
| Microsoft.WindowsAppSDK.ML | 1.8.2141 | Transitive |
| Microsoft.WindowsAppSDK.Runtime | 1.8.260317003 | Transitive |
| Microsoft.WindowsAppSDK.Widgets | 1.8.251231004 | Transitive |
| Microsoft.WindowsAppSDK.WinUI | 1.8.260224000 | Transitive |
| System.Numerics.Tensors | 9.0.0 | Transitive |

The actual package also contains `onnxruntime.dll` (21,556,080 bytes), `DirectML.dll` (18,548,584 bytes), `Microsoft.Windows.SDK.NET.dll` (26,341,408 bytes) and the .NET runtime, including `coreclr.dll` and `System.Private.CoreLib.dll`. These are **shipped binary evidence**, not a finding that every referenced package contributes an independent redistributable or that the licenses allow release.

## Unresolved release and acceptance conditions

1. Map the exact 319 candidate paths and all other relevant runtime/resources to their owners, source packages and applicable license/EULA (including component-level Microsoft Windows App SDK, .NET Windows **.NET Library License**, notices, ML/DirectML/ONNX and WebView2 conditions). Separate build-only NuGet references from shipped files.
2. Preserve and actually bundle all required license/notice texts; prove they correspond to the exact shipped binaries and their hashes. Check Microsoft version-specific redistribution terms independently. Do not infer clearance from successful CI, the NuGet list, OHA MPL-2.0 or the ZIP's existence.
3. Evaluate whether unused ML/AI runtime components can be omitted *without breaking WinUI deployment*, but only as a separate, fully retested scope change. Do not assume modular trimming is safe or legally required.
4. Perform actual Windows/macOS device GUI acceptance per [#16](https://github.com/StanleyLl0yd/OHA/issues/16). Hosted native compilation, hash verification, CodeQL and ad-hoc signing are not physical tests.
5. Obtain accountable owner/legal review on complete binary distribution terms. Keep [#40](https://github.com/StanleyLl0yd/OHA/issues/40) and M0 **OPEN**; do not start M1 without separate M0 acceptance.

No downloaded ZIP bytes are committed to the repository. The counts above are specific to the exact workflow run and must be regenerated for any modified preview or eventual release.
