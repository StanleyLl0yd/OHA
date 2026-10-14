# OHA native interface contract - M0 proposal

Status: design only; does not define a released binary ABI.

## Boundary

- Rust is the single source of truth for archive jobs, codec policy, manifests, settings schemas, errors and capability negotiation.
- Windows WinUI 3 / C# calls a C ABI through P/Invoke; macOS SwiftUI/AppKit calls the same C ABI through a Swift-friendly generated bridge.
- The Linux and bundled cross-platform CLI use the Rust API directly.
- No GUI calls internal decoder symbols. File paths and progress messages cross one documented boundary.

## Proposed ABI operations

```c
// Names, signatures and types are PROPOSALS, not stable ABI symbols.
// All strings use explicit (pointer, length) UTF-8 byte spans.
// No Rust-managed pointer is retained by the caller without documented ownership.

uint32_t oha_api_version(void);
int32_t  oha_context_new(const oha_options_v1 *options, oha_context **out);
int32_t  oha_context_close(oha_context *ctx);
int32_t  oha_job_start(oha_context *ctx, const uint8_t *request, size_t request_len, oha_job **out);
int32_t  oha_job_poll(oha_job *job, oha_event_v1 *out);
int32_t  oha_job_cancel(oha_job *job);
int32_t  oha_job_close(oha_job *job);
void     oha_buffer_free(uint8_t *buf, size_t len);
```

Do not use this example header to build a shipping application. For actual implementation, choose an exact stable integer width for lengths and clarify allocators, versioned struct size, call safety and lifetimes.

## Lifecycle

`create context -> start async job -> poll bounded events -> wait for completion -> close job -> close context`.

- Handles are opaque and cannot be forged as raw integers.
- Every API validates handle lifecycle and buffer lengths. Closing an active job cancels and joins or delegates bounded cleanup as specified.
- Polling returns *structured* events with monotonically increasing sequence IDs. Progress events may be coalesced to bound memory. Terminal states cannot be discarded.
- Errors include machine-readable code, message key, optional localized text from GUI and safe diagnostic detail. Never include plaintext file content/passwords.
- Cancellation is idempotent and does not imply rollback has completed. A separate terminal event confirms safe stopping and cleanup.
- Any panic inside Rust crossing FFI is an ABI bug. Catch/translate panics at entry boundaries and isolate further if necessary.
- Callback-free poll API is preferred for first release to simplify native UI thread handoff. UI clients poll off UI thread and marshal updates onto the appropriate dispatcher/MainActor.
- Capability discovery includes available codecs, feature flags and decoder memory requirements; unknown operations fail explicitly.

## Priorities for prototype

1. C ABI `version`/`context_new`/`close` and byte buffer ownership.
2. `analyze-file` job returning metrics without exposing Rust-specific types.
3. Progress/cancel and error marshalling on Windows and macOS.
4. A native large-file virtualized file-list with 100k synthetic entries in each UI.
5. Negative tests: invalid pointers, double-close, concurrent cancel/poll, oversized event, UI event loop not blocked.

## M0 implemented experimental ABI probe (not the proposed job API)

`crates/oha-ffi` exposes `oha_api_version()` and synchronous `oha_analyze_bytes_v1(input, length, output)` as a `cdylib`. Its fixed C layout is defined in `include/oha_ffi.h`. The caller owns input/output memory, passes `struct_size=72` and `version=1`, and receives a numeric status and descriptive metrics. Input is capped at 192 KiB. Empty/null input is accepted only at length zero. Non-null invalid pointers are caller-contract violations and cannot be safely detected or recovered from. Non-overlap and alignment are mandatory; Rust does not retain or free pointers. The entrypoint catches Rust panics and returns a status, but **this is not process isolation**.

Rust unit tests and Python `ctypes` foreign-language tests verify the ABI on Linux x64, Windows x64, macOS ARM64 and macOS Intel. The native WinUI 3 and SwiftUI/AppKit graphical clients, long-running jobs and cancellation protocol remain M0 work. This synchronous probe is **not** an archive parser, stable public ABI, or production API.

## Native GUI shells (M0, pending CI verification)

`apps/oha-windows` and `apps/oha-macos` are minimal native WinUI 3/C# and SwiftUI/AppKit visual shells. Both invoke the bounded existing `oha-ffi` C ABI over a fixed UTF-8 sample without retaining raw pointers. They do not open user files, create archives, implement jobs/cancel/progress, or define a shipping ABI. See `docs/NATIVE_UI_M0.md`. CI attempts native Windows x64 and macOS arm64/x86_64 builds plus separate Swift-to-Rust execution; interactive GUI tests remain pending.
