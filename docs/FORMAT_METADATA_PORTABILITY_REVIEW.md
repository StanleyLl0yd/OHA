# M0 decision brief: portable file metadata for candidate `.oha`

**STATUS: RESEARCH ONLY, OWNER DECISION REQUIRED.** This document does not approve, allocate, or implement any on-disk format. It is a review companion to [the tentative CBOR metadata schema](FORMAT_METADATA_CBOR_PROPOSAL.md), [wire framing proposal](FORMAT_V1_PROPOSAL.md), and issue [#5](https://github.com/StanleyLl0yd/OHA/issues/5). Do not produce `.oha` files from these layouts. M1, not M0, implements a writer/reader after approval.

## Confirmed gap

The currently implemented **read-only** research manifest checks the shape `[1, [[path, kind, size, segments]...]]`. It has no fields for file or directory modification time, POSIX executable/permission bits, or Windows read-only semantics. A future writer using that schema alone would necessarily lose basic metadata. That conflicts with OHA's no-silent-loss product invariant. Valid file bytes and path mappings **do not** establish a suitable user archive.

The current restricted CBOR parser accepts unsigned integers only (major type 0), bytes/text and definite arrays. It intentionally rejects negative integers (major type 1). Pre-1970 modification times therefore cannot fit an ordinary signed epoch representation without a **new metadata schema and parser proposal**. The existing test fixtures and proposed structural vectors are not interoperability tests.

## Recommended decisions for review (none approved)

| Question | Recommended candidate | Alternative / consequence |
|---|---|---|
| Schema evolution | Amend the **unapproved** MNFT schema and bump its own schema version before any writer, leaving INDX separately versioned | Keeping the current `MNFT 1` permanently would force warnings/errors for all unsupported basic metadata or later incompatible workarounds |
| Modification time | Preserve file **and directory** mtime using a pair of signed UTC/POSIX epoch seconds + unsigned nanoseconds 0..999,999,999 | A signed single 64-bit nanosecond count excludes Windows' earliest FILETIME-era dates (1601); truncated seconds lose available precision |
| CBOR representation | Deterministic RFC 8949 definite arrays; support minimal CBOR negative integers *only in explicitly typed signed-second positions*, preserving existing restricted unsigned fields | A custom LE TLV also works but commits to a bespoke parser and a separate independent byte-vector corpus |
| Unknown mtime | Explicit absence marker or empty field distinct from Unix epoch zero, with a warning/policy when capture or restore is unavailable | Silently substituting the current clock/epoch corrupts metadata semantics |
| Executable / POSIX permissions | Preserve at least the portable `rwx` permission bits for regular files/directories, with an explicitly bounded integer and target-aware restore policy | Omitting execute bits can make unpacked scripts/tools unusable; blindly applying arbitrary mode bits or privileged ownership is unsafe |
| Windows read-only | Preserve an explicit portable readonly hint separately from POSIX `rwx` mode, document precedence on target OS | Windows DOS read-only and POSIX owner/group/world write bits are not losslessly interchangeable |
| Unsupported extras | Enumerate unsupported ACLs, owners, xattrs, NTFS ADS, macOS resource forks/Finder tags, birthtime and sparse allocation as explicit **warning or error** (strict mode errors) | Never claim full fidelity for these without versioned, tested support |
| Path fidelity | Preserve exact admitted NFC UTF-8 relative names; **reject** names not representable by the accepted cross-platform policy, without silently replacing Unicode or bytes | Lossless reversible mapping for nonportable POSIX names would require a separately approved mapping contract |
| Extraction safety | Restore regular-file data atomically under a guarded destination; apply metadata only to safely opened handles; restore **directory mtime after children**; avoid setting privileged bits/ownership | String-only path prevalidation cannot prevent symlink races; root-relative no-follow operations are required |
| Error policy | Distinguish unsupported source metadata, corrupted archive fields, target incompatibility and user-selected loss policy; record per-entry errors | Silent best-effort extraction must not masquerade as a fully verified round-trip |

## Timestamp edge cases required in independent vectors

If the owner approves seconds + nanoseconds, demand negative pre-epoch seconds, exact epoch zero, post-2038 dates, 1601-era representable times, nanosecond boundary values `0` and `999999999`, unknown/unavailable timestamps, file vs directory order, and different host filesystem precisions. Define negative-fraction normalization explicitly: e.g. 1969-12-31T23:59:59.500Z = seconds `-1`, nanoseconds `500000000`. Decoders must reject overflow, invalid nanos, non-minimal CBOR and out-of-range host timestamps; no clamping without explicit user-visible policy.

The chosen **wire representable range**, **decoder resource limits** and **host filesystem supported range** are three different constraints; a 64-bit seconds field must not cause an unbounded allocation or force an OS API to accept ancient dates. Timestamps describe metadata, never executable instructions.

## Proposed acceptance scenarios for M1 (not implemented)

1. Capture and restore ordinary file+directory mtime on Windows, macOS and Linux where representable, independently verify at the supported filesystem resolution and report any precision loss.
2. Preserve cross-platform readonly and executable/permission behaviors where policy permits; safely reject nonportable or privileged metadata.
3. Reject malformed negative CBOR arguments, reserved flags, duplicate fields, invalid absent/present combinations and unsupported mandatory versions without reading beyond declared budgets.
4. Test empty files/directories, nested directory timestamp restoration after writing children, permission changes, interrupted extraction and symlink/race attacks with real filesystem handles.
5. Prove exact file-byte round-trip independently of metadata, with truthful reporting of each unsupported attribute rather than silently discarding it.

## Upstream reference points

- [RFC 8949, Sections 3.1 and 4.2](https://www.rfc-editor.org/rfc/rfc8949.html#section-4.2): CBOR major type 1 represents negative integers as `-1 - argument`; deterministic encoding requires minimal integer/length representation. Any new timestamp field must define this precisely.
- [Microsoft FILETIME specification](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-dtyp/2c57429b-fdd4-488f-b5fc-9e4cf020fcdf): Windows file times are UTC-relative, in 100 ns units since January 1, 1601. This is why the proposed *signed seconds plus subsecond nanos* representation has a different range/precision trade-off from single signed-64 nanoseconds.
- [Microsoft file timestamp notes](https://learn.microsoft.com/en-us/windows/win32/sysinfo/file-times): filesystem differences (including NTFS vs FAT local-time handling) require explicit precision/portability error behavior. This is a candidate policy, not an adopted compatibility guarantee.

## Approval checklist

Owner must explicitly accept or modify the schema version and field ordering, deterministic CBOR subset, time representation and precision, portable mode/readonly policy, unsupported attribute policy, filename restrictions, permanent format maxima vs adjustable reader budgets, and ZSTD/codec compatibility. Only then can independently generated golden bytes and negative test vectors be frozen. The present probes remain research-only, do not extract, and **cannot** authenticate compressed DATA.

Issue #5 and milestone M0 remain **OPEN** until signed-off decisions and the remaining acceptance criteria. No format writer, decoder, or M1 implementation is authorized by this review.
