# Third-party components and redistribution status

OHA project-owned source is licensed under [MPL-2.0](LICENSE). **This is a preliminary inventory, NOT full legal clearance to distribute each binary artifact.**

| Component | Current role | License/distribution status |
|---|---|---|
| Local OHA Rust crates | Cargo.lock currently lists four OHA crates, no external crates | Original source MPL-2.0 |
| Microsoft.WindowsAppSDK 1.8.260317003 | Self-contained Windows x64 preview may bundle proprietary runtime files | Microsoft license and Section 3 redistribution conditions must be checked; https://www.nuget.org/packages/Microsoft.WindowsAppSDK/1.8.260317003/License |
| Microsoft.Windows.SDK.BuildTools 10.0.26100.7175 | Windows build tool | Verify which components, if any, ship in a preview |
| .NET/WinRT components | Windows preview runtime | Transitive versions and license files require actual binary inventory |
| Apple SwiftUI/AppKit | OS frameworks used by macOS preview | Platform terms apply; not relicensed |
| 7-Zip, ZSTD, XZ | External benchmark commands | Not shipped inside OHA binaries |
| Canterbury corpus mirror | CI benchmark material | Downloaded transiently; not included in OHA archive artifacts |

Prior to any production/release redistribution, enumerate **actual** included DLLs/dylibs/runtime binaries and required complete third-party notices/license texts; review Microsoft and any other vendor-specific EULAs. Do not label third-party runtime binaries MPL-2.0. Candidate libzstd/liblzma/liblz4/BZip3/7-Zip licensing details in [docs/LICENSING_RESEARCH.md](docs/LICENSING_RESEARCH.md). Issue #4 stays OPEN until this separate release gate is met.
