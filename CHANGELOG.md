# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This project maintains **two independent version numbers**:

| Version | Scope | Description |
|---------|-------|-------------|
| **Spec** | File format (in `metadata.json`) | Format stability — changes require formal proposal |
| **Tool** | CLI (`aidoc --version`) | Tool iteration — bug fixes, new features |

Both start at 0.1.0 in this initial release.

---

## [Spec 0.1.0 / Tool 0.1.0] — 2026-04-29

### Added

- **AIDOC container format** — Standard ZIP with content.md as first entry for AI-optimized reads
- **Two-level versioning** — Spec version (format stability) separated from Tool version (iteration speed)
- **Standard governance** — Version lifecycle (pre-release → stable → evolution), change proposal process, deprecation policy, stability promises
- **CLI tool** (`aidoc`) with 11 commands:
  - `init` — Create blank AIDOC from template
  - `create` — Pack files (MD, Word, PDF, images) into AIDOC
  - `md` — Fast read of Markdown content (AI-optimized, ~10μs)
  - `ls` — List files inside container
  - `meta` — View metadata
  - `info` — Combined meta + ls
  - `check` — Validate AIDOC format
  - `extract` — Extract all files
  - `sign` — Digital signing (PKCS#7 / SM2)
  - `verify` — Signature verification + integrity check
  - `view` — Web-based document reader with Markdown/original toggle
- **Fast Read algorithm** — Skips ZIP Central Directory; 2.3–2.9× faster than standard ZIP
- **Digital signing** — PKCS#7 detached signature (RSA, ECDSA) + SM2 (via gmssl)
- **Self-signed test certificate generation** (`--gen-key`)
- **Tamper detection** — SHA-256 manifest + signature validation
- **Full specification** (SPEC.md) — Container structure, compression strategy, extension mechanism, governance
- **Bilingual documentation** — Chinese and English user guides
- **Performance benchmark** — Reproducible benchmark script with detailed results
- **Cross-platform web reader** (`aidoc view`) — Browser-based with Markdown/original toggle
- **CI Pipeline** — GitHub Actions (Python 3.9–3.12, full test suite)
- **Contributing guide** — Development workflow, code style, submission process
- **MIT License**

[Spec 0.1.0 / Tool 0.1.0]: https://github.com/your-username/aidoc/releases/tag/v0.1.0
