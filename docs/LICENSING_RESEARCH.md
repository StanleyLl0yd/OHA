# Third-party codec license research (M0, 2026-10-14)

This is an inventory of candidate upstream projects, **not** a legal clearance or a final OHA license decision. No candidate native compression library is currently linked into the workspace, and benchmark command-line programs are not redistributed. Confirm the exact version, wrapper/source files, static/dynamic model, notices and distribution requirements before adding dependencies.

| Candidate | Upstream license finding | OHA action |
|---|---|---|
| `zstd` / `libzstd` | Reference library offered as BSD-3-Clause **OR** GPL-2.0 licensing; BSD requires notices for binary distribution | Prefer permissive option for prospective M1 integration; audit specific Rust wrapper and build mode |
| `xz` / `liblzma` | Upstream `liblzma` and core CLI in modern XZ Utils are 0BSD; accompanying tools/scripts may use other licenses | Candidate M2 LZMA2 backend, version-specific file/component check required |
| `bzip3` | Upstream states project LGPL-3.0; bundled components have other licenses | Keep deferred; assess relinkability, attribution and App Store packaging before importing |
| Full `7-Zip` sources | Predominantly LGPL-2.1-or-later, separate parts BSD; RAR decoder parts carry additional unRAR restriction | Baseline tool only. Do not copy the full archiver or restricted RAR components into OHA by assumption |

Upstream sources checked:
- https://github.com/facebook/zstd/blob/dev/LICENSE
- https://github.com/facebook/zstd/blob/dev/README.md
- https://github.com/tukaani-project/xz/blob/master/COPYING
- https://tukaani.org/xz/liblzma-api/index.html
- https://github.com/iczelia/bzip3/blob/master/LICENSE
- https://github.com/iczelia/bzip3
- https://github.com/ip7z/7zip/blob/main/DOC/License.txt

**Project license still requires owner approval.** A possible decision to review is dual MIT/Apache-2.0 (familiar to Rust projects), with a separate third-party notices directory. Do not add a `LICENSE` file until approved.
