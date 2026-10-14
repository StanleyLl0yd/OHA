# OHA Agent Rules

Root instructions for automated coding agents. The owner's explicit current instructions override this document. Keep this file focused; refer to accepted ADRs and security documentation for detailed invariants.

## Product invariants

- Product: OHA (Optimized Hybrid Archiver); own format `.oha`; no alpha/beta/rc suffixes, only numeric versions.
- Native Windows GUI: WinUI 3/C#. Native macOS GUI: SwiftUI with AppKit/Swift. Linux: feature-complete CLI for supported core capabilities, no GUI in the initial scope.
- Rust owns compression, container, deduplication, crypto, manifest handling and all application/business state; the two GUIs are thin clients.
- Absolutely no required server, cloud account, remote processing, telemetry or online dependencies for archiving or extraction.
- Avoid `oha` CLI alias because it conflicts with an established HTTP load tester; default executable `oha-archiver`.
- `.oha` compatibility is controlled by magic/version/capability contracts, not extension alone.
- Treat every archive and every archive metadata field as untrusted. Bounds before allocation, safe path handling, no arbitrary code execution from archives.
- Do not invent a compression algorithm, custom cryptographic primitive or stable binary specification prematurely. Prefer reviewed libraries and document all license obligations.
- Never silently lose original bytes, file versions or platform metadata. Unsupported restoration must be explicit.
- Do not add an OSS LICENSE file until the owner approves one. No guessed redistribution permission.

## Work discipline

1. Start by inspecting repository structure, manifests, versioned contracts, tests and current milestone. Do not reread unchanged material repeatedly.
2. Work in small, reviewable task branches; favor scoped changes and compatibility tests.
3. Keep `main` buildable. Do not change format semantics without a versioned migration and test vectors.
4. Pin dependencies and CI actions; commit lockfiles where appropriate. Check licenses, provenance and supply-chain implications.
5. Run targeted checks first and expand. Never claim unrun checks passed.
6. For codec-policy experiments, prevent benchmark overfitting; compare against independent baselines and report real data/measurement context.
7. Keep platform GUI code free of archive decision logic. FFI must have stable ownership and error boundaries; Rust panic must never unwind through FFI.
8. Preserve security, compatibility, Windows/macOS/Linux parity. Do not start next milestone until exit gate passes.

## Mandatory complete repository-wide audit and deep-refactoring protocol

A user request for a **full audit, security audit, cleanup, optimization, code review or refactoring of the project/repository** means a full pass over the *entire* repository, not merely the latest diff or familiar problem areas.

Scope: all production code, tests, tooling, build/CI/release scripts, manifests, dependencies, resources, docs, platform integrations, FFI, compatibility, file-format/security rules and configuration. Establish actual architecture, behavior, public APIs, persistence and platform constraints before changing things.

Look for proven dead/unreachable code, unused imports/dependencies/assets/configuration, obsolete legacy/flags/workarounds, duplicated logic, redundant conversions, abstraction chains, avoidable allocations and unnecessary complexity. Do not treat absence of textual references as proof of dead code; check reflection, events, callbacks, generated code, configs, manifests, serialization, OS integration and other indirect entry points.

A change is justified only if it demonstrably reduces necessary complexity, duplication, coupling, maintenance or risk, or measurably improves performance, **while preserving user-visible behavior and security**. Do not rewrite for style, chase line count, remove established fallbacks without proof, or speculate abstractions into existence. If a removal is uncertain, leave it intact and document why.

Required method:
1. Inspect the whole repository and establish baseline/test coverage.
2. Record candidate removals/consolidations/simplifications/dependency cleanup and rank by confidence and risk.
3. Add minimum regression tests before risky behavior-preserving changes where coverage is inadequate.
4. Implement improvements in coherent groups; run relevant tests and checks after each group.
5. Complete the first pass, then **conduct a second full repository-wide pass** looking for remaining/revealed dead code, duplication and unnecessary structure.
6. Run the complete available verification suite including cross-platform core tests, formatter, lint, build, integration, format compatibility, fuzz/security/static/dependency checks where applicable.
7. Report removed, consolidated, simplified, dependencies, legacy, deliberately unchanged code, verification evidence, limitations and reliable before/after measurements. Never invent statistics or report unrun checks as passed.

## Mandatory milestone exit verification

On completion of **every** milestone (M0, M1, M2, ...), perform the full repository-wide audit, code review and simplification/refactoring protocol above. Include security and format-compatibility assessment appropriate to the milestone. Execute all mandatory CI and platform checks. A milestone may be marked complete only with recorded audit findings, changes or justified no-op, verification evidence, and final-main CI confirmation. A limited test release does not imply milestone completion.

## Priority of trusted documents

Current owner instruction > AGENTS.md > accepted ADRs > docs/SECURITY.md > docs/ARCHITECTURE.md > docs/ROADMAP.md > README. Unknown contract conflicts must be surfaced rather than silently overridden.
