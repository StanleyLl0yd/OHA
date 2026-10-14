# ADR 0003 - Compression strategy

Status: Proposed (2026-10-14)

- No codec universally wins. Candidate list should depend on data characteristics and resource budgets.
- Optimize **total byte cost including headers, dictionaries and index**, not compressed payload alone.
- Use a Pareto front for compressed size, CPU times and memory. Profiles choose a point on that front.
- Base candidates: STORE, ZSTD; add LZMA2 after instrumentation, then optional BZip3 if its licensing and benefits are established.
- Sampling has a strict CPU and byte budget. Verify chosen final output and fall back to STORE when compression cannot amortize total overhead.
- Keep 7-Zip, ZSTD and raw STORE independent baselines. Define evaluation sets before tuning to prevent benchmark overfitting.
