# M0 local GUI preview bundles

This is an **experimental, unsigned/non-notarized** source-only product prototype. The `M0 Native Preview Artifacts` workflow creates short-retention GitHub CI artifacts for owner-driven testing. These are *not* an OHA release or a functional archive utility. No pack, extract, list or archive encryption operations are implemented.

## Windows x64

The Windows GitHub-hosted runner publishes an unpackaged, self-contained WinUI 3/.NET 10 folder with the matching Rust `oha_ffi.dll`. Extract the `OHA-M0-Windows-x64.zip` preview, keep all files together, and run `OHA.Windows.exe`. No Windows App SDK runtime installer should be necessary for the self-contained output, but the package has **not** been tested on a user desktop. Executables are not Authenticode-signed; SmartScreen warnings may apply. Inspect the GitHub Actions build provenance and `SHA256SUMS.txt` before local evaluation. Preview does not install itself or associate file types.

Official Windows App SDK unpackaged/self-contained guidance: https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/unpackage-winui-app and https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/self-contained-deploy/deploy-self-contained-apps

## macOS

The macOS ARM64 and Intel runners package a minimal SwiftUI executable as `OHA.app` with the matching Rust dynamic library embedded under `Contents/Frameworks`, relative linker dependency, Info.plist and ad-hoc local signature. Extract the nested `OHA-M0-macOS.zip` using `ditto` when possible to preserve bundle metadata. This is **not** signed using a Developer ID certificate and is **not** notarized; Gatekeeper may reject opening it without the owner's explicit local security exception. Never claim the ad-hoc signature establishes publisher identity. Actual launching, UI behavior and cross-machine compatibility remain to be checked.

## Verification / limitations

The workflow verifies that the published Windows EXE and Rust DLL are present, and on macOS checks the linked library path and verifies the ad-hoc bundle signature. Each preview includes SHA-256 hashes for its key content. The required CI `verify` already tests core/native builds and actual Rust FFI smoke. This preview workflow is *not* a substitute for interactive acceptance, installer signing, notarization, security audit, or M0 exit criteria. Keep Issue #6 OPEN until owner testing and agreed packaging targets are validated.
