# Import scaffold into a new GitHub repository

The connected GitHub tooling cannot create a new repository. `StanleyLl0yd/OHA` did not exist at the time this scaffold was prepared. No remote commits/PRs were made.

Suggested new repository fields:

- **Name:** `OHA`
- **Description:** `Optimized Hybrid Archiver: an offline, cross-platform intelligent data archiver with native Windows/macOS interfaces and a Rust CLI.`
- **Visibility:** owner choice. Do not infer any license from public visibility.
- **Initialize with README/license:** No, this scaffold has README; license decision pending.
- **Topics:** `archiver`, `compression`, `rust`, `cross-platform`, `data-compression`, `backup`, `deduplication`, `windows`, `macos`, `linux`.

Import locally after examining the scaffold. The following are example commands, **not already executed**:

```sh
git init -b main
git add .
git commit -m "docs: initialize OHA M0 research scaffold"
gh repo create StanleyLl0yd/OHA --public --source=. --remote=origin --push
```

If the owner chooses a private repository, use `--private` instead of `--public`. Do not add a `LICENSE` until approved. Before protecting `main` verify CI on all three systems, ensure default branches and security rules, then require PR review/CI for subsequent development.

After repository creation, immediately run/pin Rust toolchain and fix any Windows/macOS portability issues found by CI. Generate and commit Cargo.lock to make tooling reproducible, and open focused issues for outstanding M0 gates from `docs/ROADMAP.md`.
