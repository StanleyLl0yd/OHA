# Adaptive decision engine: research contract

## Objective

Choose an admissible compression **plan** rather than a single favorite codec. A plan specifies chunk/group boundaries, reversible transforms, codec, parameters, dictionary scope, random-access granularity, and decoder resource needs.

Plan quality is measured over **the entire archive**, including structural metadata, common dictionaries, embedded dictionary bytes, compression payloads, indexes and authentication overhead (if enabled).

## Inputs

- Workload type: one-shot archive or versioned backup.
- File types identified from content and magic, not extension alone.
- Bounded samples, estimated structure/repetition, high-entropy areas, cross-file similarity and sample-codec results.
- User profile: fast / balanced / maximum / extreme / backup.
- Resource budget: max RSS, allowed CPU/wall time, desired extraction latency, thread count, target decoder memory ceiling.
- Capability registry: codec IDs with exact decoder versions and platform support.

## Phase 1 (M0/M1): deterministic selection

1. Analyze only bounded bytes. For huge files use spaced samples. Do not force all files into RAM.
2. Classify content and generate a small candidate set. `STORE` must always be admissible.
3. Run short compression probes for candidates permitted by resource budget.
4. Measure bytes and elapsed time; estimate decoder cost through a separate calibration table. Do **not** treat compression speed as a proxy for decompression.
5. Discard candidates that violate any hard constraint.
6. Compute a Pareto front: a candidate is dominated if another has no larger archive size, time or decoder cost and is strictly better on at least one.
7. Choose profile-specific objective on Pareto front.
8. On full compression, if total output bytes including metadata are not competitive, select STORE when possible.
9. Record reason and measured candidate statistics without leaking file content.

Simple weighted cost for an optional preference profile, with dimensionally normalized terms:

`J = w_size * (total_bytes / input_bytes) + w_cpu * (compress_ms / budget_ms) + w_decode * (decode_ms / decode_budget_ms) + w_ram * (peak_ram / ram_limit)`

Hard constraints are **not** replaced by this weighted score. Zero/unknown budgets must be handled explicitly. Estimate uncertainty using holdout blocks and never assign fake precision.

## Deterministic tie behavior (M0 research)

For candidates that have exactly the same profile ranking metric, ranking must not depend on the caller's candidate array order. The current research selector uses lower decoding latency when `Balanced` otherwise ties, then a stable codec tie order `STORE`, `ZSTD`, `LZMA2`, `BZip3`. For `Fast` and `Maximum`, the codec tie rank is applied only after all their measured time/size keys are equal. This ordering is a *tie policy*, not an assertion about codec quality or license readiness. Hard resource ceilings and checked total sizes remain mandatory.

## Initial candidate policies (hypotheses to test)

| Signals | Candidate list |
|---|---|
| Unknown/mixed bytes | STORE, ZSTD |
| Repeated text/source/JSON | ZSTD, LZMA2, optional BZip3 after licensing |
| Already compressed/encoded streams | STORE, cheap ZSTD probe |
| Many tiny similar files | ZSTD trained dictionary vs bounded solid groups |
| Executable machine code | ZSTD/LZMA2, reversible BCJ when validated |
| Similar successive backup revisions | content-defined chunks + cross-version dedup; compress only new unique chunks |

Extension is only a hint. High entropy does not establish incompressibility. Dictionary training and probes are time-limited; sample quality matters more than codec count.

## Benchmarks and acceptance

Required comparisons: baseline all-STORE, ZSTD at declared levels, 7-Zip LZMA2 with explicit flags, ZSTD+solid grouping, OHA adaptive policy. Include mixed trees, varied tiny files, source code, logs, executables, PDF/media/precompressed files, nearly duplicated backups and incompressible data.

Report: produced archive bytes and metadata overhead, encoder wall and CPU time, full decode, random-file decode, peak RSS, I/O volume, verified roundtrip, per-file codec decisions and sample cost. Avoid claiming universal superiority. An improvement is credible only if replicated on independent corpora and identical resource envelopes.

## Deferred research

- Cross-file clustering heuristics, dictionary learning, dedup + solid switching.
- Online/learned selector only if added latency and model size outperform the deterministic baseline.
- Very slow PAQ/CMIX-class codecs in optional research, not mandatory default decoders.
