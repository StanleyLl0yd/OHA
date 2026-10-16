# M0 local GUI preview bundles

This is an **experimental, unsigned/non-notarized** source-only product prototype. The `M0 Native Preview Artifacts` workflow creates short-retention GitHub CI artifacts for owner-driven testing. These are *not* an OHA release or a functional archive utility. No pack, extract, list or archive encryption operations are implemented.

## Windows x64

The Windows GitHub-hosted runner publishes an unpackaged, self-contained WinUI 3/.NET 10 folder with the matching Rust `oha_ffi.dll`. Extract the `OHA-M0-Windows-x64.zip` preview, keep all files together, and run `OHA.Windows.exe`. No Windows App SDK runtime installer should be necessary for the self-contained output, but the package has **not** been tested on a user desktop. Executables are not Authenticode-signed; SmartScreen warnings may apply. Inspect the GitHub Actions build provenance and `SHA256SUMS.txt` before local evaluation. Preview does not install itself or associate file types.

Official Windows App SDK unpackaged/self-contained guidance: https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/unpackage-winui-app and https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/self-contained-deploy/deploy-self-contained-apps

## macOS

The macOS ARM64 and Intel runners package a minimal SwiftUI executable as `OHA.app` with the matching Rust dynamic library embedded under `Contents/Frameworks`, relative linker dependency, Info.plist and ad-hoc local signature. Extract the nested `OHA-M0-macOS.zip` using `ditto` when possible to preserve bundle metadata. This is **not** signed using a Developer ID certificate and is **not** notarized; Gatekeeper may reject opening it without the owner's explicit local security exception. Never claim the ad-hoc signature establishes publisher identity. The CI artifact now accompanies the nested `OHA-M0-macOS.zip` with a **separate external** `OHA-M0-macOS-SHA256SUMS.txt`. It hashes every regular file in the **signed app bundle**, including `Info.plist`, notices, executables and `_CodeSignature/CodeResources`. The workflow unpacks the final ZIP and checks complete SHA-256 coverage and `codesign --verify --deep --strict` against the **unpacked** `OHA.app`. No files are added to the signed bundle after signing. When testing, download the ZIP and sibling checksum manifest from the **same trusted run**, extract using `ditto`, and verify manifest entries against the extracted app. These hashes detect unexpected changes but are not publisher authentication, notarization or legal redistribution clearance. Actual launching, UI behavior and cross-machine compatibility remain to be checked.

## Verification / limitations

The workflow verifies that the published Windows EXE and Rust DLL are present, and on macOS checks the linked library path and verifies the ad-hoc bundle signature. The Windows preview keeps `SHA256SUMS.txt` inside its ZIP; macOS publishes a complete external signed-bundle checksum manifest beside its ZIP so the signed app remains immutable. The required CI `verify` already tests core/native builds and actual Rust FFI smoke. This preview workflow is *not* a substitute for interactive acceptance, installer signing, notarization, security audit, or M0 exit criteria. Keep Issue #6 OPEN until owner testing and agreed packaging targets are validated.

## MPL-2.0 source availability

OHA project-authored source is licensed under MPL-2.0. Native preview packages now include the original official LICENSE text, a THIRD_PARTY_NOTICES inventory, and SOURCE-CODE.txt identifying the exact GitHub commit used to build the preview. The corresponding source can be obtained at https://github.com/StanleyLl0yd/OHA/tree/<commit-id>. This is required for MPL-covered binaries and is not a substitute for the outstanding Windows App SDK runtime licensing/redistribution verification. Packages remain non-production research probes.

## Machine-readable binary inventories (M0)

Each CI preview artifact includes an external `OHA-M0-*-inventory.json` alongside its ZIP. The source-controlled `tools/preview_inventory.py` verifies MPL text, exact commit source notice, integrity checksums, required native binaries, rejects symlinks/unsupported filesystem entries and records SHA-256/size/path for every artifact file. For Windows, it also parses any bundled `.deps.json` library metadata. The inventory labels native binaries that **may** be third-party components; it deliberately does **not** assign their legal licenses or certify redistribution. The manifest is outside the macOS `.app` so Code Signing remains valid. Actual package-specific terms and end-user compliance still block product release (#4).

### Windows NuGet dependency provenance (M0)

The Windows preview workflow additionally exports `OHA-M0-Windows-x64-nuget.json` produced from `dotnet package list --project apps/oha-windows/OHA.Windows.csproj --include-transitive --no-restore --format json --output-version 1`, after the actual `dotnet publish`. This records NuGet top-level and transitive package versions alongside the separate per-file binary SHA-256 inventory. The format is defined by the [.NET CLI documentation](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-package-list). Package references include build-only dependencies, and a package may contribute many runtime files or none. The two inventories must **not** be naively equated. This is technical input for the release license audit, **not** a vetted SBOM, a legal attribution file, evidence of allowed redistribution or a replacement for required full license notices and Microsoft terms. #4 remains open.
