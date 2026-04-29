# AIDOC — AI-Native Document Format User Guide

> **Version**: 0.1.0 · **Updated**: 2026-04-29

---

## Table of Contents

1. [Overview](#1-overview)
2. [Installation](#2-installation)
3. [Quick Start](#3-quick-start)
4. [Command Reference](#4-command-reference)
5. [Digital Signing](#5-digital-signing)
6. [AI Toolchain Integration](#6-ai-toolchain-integration)
7. [How It Differs from Plain ZIP](#7-how-it-differs-from-plain-zip)
8. [FAQ](#8-faq)

---

## 1. Overview

### 1.1 What is AIDOC?

AIDOC (AI Document) is an **AI-native document container format**. It bundles the human-readable original document with an AI-optimized Markdown representation and structured metadata in a single ZIP file. Both AI and humans can work with the same document in their most comfortable way.

```
report.aidoc/
├── content.md          ← 🚀 AI reads this directly (STORED, 1st entry)
├── metadata.json       ← 📋 Structured metadata
├── document.docx       ← 📄 Original Word document
└── cover.png           ← 🖼️ Attached image
```

### 1.2 Core Design Principles

| Principle | Description |
|-----------|-------------|
| **content.md is first** | Always the first ZIP entry. AI reads it without parsing Central Directory |
| **STORED (no compression)** | Markdown is tiny; no compression means zero-overhead reading |
| **Pure standard ZIP** | No ZIP hacks. Any ZIP tool can open AIDOC files |
| **Digital signing** | Supports PKCS#7 / SM2 for authenticity and integrity |

### 1.3 Use Cases

- **AI report generation** → Output .aidoc. AI reads MD for summaries, humans open original in Word
- **Document archiving** → One file with both original and AI-generated abstract
- **Financial compliance** → Signatures prevent tampering; audit trail is built-in
- **Knowledge base management** → AI indexes MD directly; no need to parse PDF/Word

---

## 2. Installation

### Option 1: Direct Use

```bash
git clone https://github.com/your-username/aidoc.git ~/Source/aidoc
export PATH="$HOME/Source/aidoc/bin:$PATH"
```

### Option 2: pip Install

```bash
cd ~/Source/aidoc/src
pip install .
aidoc --version
```

### Dependencies

| Feature | Dependency | Install |
|---------|-----------|---------|
| Core (pack/read/extract) | None (stdlib only) | Built-in |
| Digital signing (RSA/ECDSA) | openssl (system) | Built-in |
| Generate test certs | `cryptography` | `pip install cryptography` |
| SM2 signing | `gmssl` | `pip install gmssl` |

---

## 3. Quick Start

### 3.1 Create an AIDOC from Markdown

```bash
# Create a Markdown file
cat > mydoc.md << 'EOF'
# My Document

This is my first AIDOC document.

## Section 1

Some content...
EOF

# Pack it as .aidoc
aidoc create mydoc.md -o mydoc.aidoc --author "Yu Shen" --tags "AI,document"
```

### 3.2 AI Reads the Content

```bash
# 🚀 Fast read mode
aidoc md mydoc.aidoc
```

### 3.3 Inspect Metadata and Files

```bash
# View metadata
aidoc meta mydoc.aidoc

# List all files
aidoc ls mydoc.aidoc
```

### 3.4 Extract Original Files

```bash
aidoc extract mydoc.aidoc ./output
```

### 3.5 More Creation Options

```bash
# Create a blank template
aidoc init -o template.aidoc --title "Template"

# Pack Word + image
aidoc create report.docx figure1.png -o report.aidoc

# Pack Word + Markdown summary + cover image
aidoc create report.docx summary.md cover.png -o report.aidoc
```

---

## 4. Command Reference

### 4.1 `aidoc init`

Create a blank AIDOC from template.

```bash
aidoc init [-o OUTPUT] [--title TITLE]
```

**Options**:
| Option | Description | Default |
|--------|-------------|---------|
| `-o` | Output path | `untitled.aidoc` |
| `--title` | Document title | `Untitled` |

### 4.2 `aidoc create`

Pack files into an AIDOC container.

```bash
aidoc create <files...> [-o OUTPUT] [--title TITLE] [--author AUTHOR] [--tags TAGS]
```

**Options**:
| Option | Description |
|--------|-------------|
| `<files...>` | One or more files. .md/.markdown → content.md; .docx/.pdf etc → document.{ext}; others → attachments |
| `-o` | Output path (auto-generated from title if omitted) |
| `--title` | Document title (auto-inferred from filename) |
| `--author` | Author name |
| `--tags` | Comma-separated tags |

**File Classification**:
| Extension | Classification | Internal Name |
|-----------|---------------|---------------|
| `.md`, `.markdown` | Markdown content | `content.md` / STORED |
| `.docx`, `.doc`, `.pdf`, `.xlsx`, `.xls`, `.pptx` | Original document | `document.{ext}` / STORED |
| Others (.jpg, .png, .zip, etc.) | Attachments | Original name / STORED |

### 4.3 `aidoc md`

Read the Markdown content (AI-optimized mode).

```bash
aidoc md <file.aidoc>
```

**Features**:
- 🚀 **Fast path**: skips ZIP Central Directory — ~10μs per read
- Falls back to standard ZIP read if fast path fails

### 4.4 `aidoc ls`

List all files in the container with compression info.

```bash
aidoc ls <file.aidoc>
```

Sample output:
```
  Name                             Raw Size    Actual Size  Mode
  ────────────────────────────── ────────── ────────── ────────
  content.md                          1,117 B      1,117 B STORED
  metadata.json                         164 B        123 B DEFLATED
  manifest.json                         230 B        186 B DEFLATED
  signature.p7s                      1,316 B      1,316 B STORED
  ────────────────────────────── ────────── ────────── ────────
  Total                               2,827 B      2,742 B  Ratio: 97.0%
```

### 4.5 `aidoc meta`

View metadata.

```bash
aidoc meta <file.aidoc>
```

### 4.6 `aidoc info`

View metadata + file listing (combined meta + ls).

```bash
aidoc info <file.aidoc>
```

### 4.7 `aidoc check`

Check if a file is a valid AIDOC.

```bash
aidoc check <file.aidoc>
```

### 4.8 `aidoc extract`

Extract all files from the container.

```bash
aidoc extract <file.aidoc> [output_dir]
```

### 4.9 `aidoc view`

Read AIDOC documents in a web-based reader with Markdown/original toggle.

```bash
aidoc view <file.aidoc>
```

**Features**:
- 🌐 **Cross-platform** — macOS / Windows / Linux, opens automatically in browser
- 📝 **Markdown rendering** — Formatted display of document content
- 📄 **Toggle to original** — Switch to view the original document in browser
- 📋 **Metadata panel** — Document info and file list on the right side
- 🚀 Local HTTP server starts automatically, cleans up on exit

---

## 5. Digital Signing

### 5.1 Sign

```bash
# Generate test cert and sign (for development/testing)
aidoc sign report.aidoc --gen-key

# Sign with enterprise CA certificate
aidoc sign report.aidoc --cert mycert.pem --key mykey.pem

# Sign with SM2 (Chinese national standard)
aidoc sign report.aidoc --cert sm2.pem --key sm2.pem --sm2
```

### 5.2 Verify

```bash
aidoc verify report.aidoc
```

Output (success):
```
  ✅ Signature valid — file is authentic, not tampered
    Subject: CN=AIDOC Test Cert, O=AIDOC
    Issuer:  CN=AIDOC Test Cert, O=AIDOC
    Validity: Apr 29 2026 — Apr 29 2027
    Algorithm: sha256
    Signed at: 2026-04-29T09:15:22
```

Output (tampered):
```
  ❌ File has been tampered!
     Reason: Verification failure
```

### 5.3 Supported Algorithms

| Algorithm | Command | Dependency |
|-----------|---------|------------|
| RSA-2048/SHA-256 | `aidoc sign --cert c.pem --key k.pem` | openssl |
| ECDSA P-256/SHA-256 | `aidoc sign --cert c.pem --key k.pem` | openssl |
| SM2/SM3 | `aidoc sign --cert c.pem --key k.pem --sm2` | openssl |

---

## 6. AI Toolchain Integration

### 6.1 Fast Read Algorithm

The core optimization: **content.md is the first ZIP entry**, stored with `ZIP_STORED`, with no data descriptor and no extra field. This means the data offset is a fixed 40 bytes.

The AI reads it with just 3 steps:

```python
def read_md_fast(path):
    with open(path, 'rb') as f:
        header = f.read(30)                     # Read local file header
        fn_len = int.from_bytes(header[26:28], 'little')
        ext_len = int.from_bytes(header[28:30], 'little')
        data_offset = 30 + fn_len + ext_len      # Calculate data offset
        data_size = int.from_bytes(header[18:22], 'little')
        f.seek(data_offset)                      # Direct seek
        return f.read(data_size).decode('utf-8') # Read Markdown
```

**Performance**: ~**10.8μs** per read, **2.5× faster** than standard ZIP reading.

### 6.2 Python Integration

```python
import subprocess

# Read MD content
md = subprocess.run(
    ['aidoc', 'md', 'report.aidoc'],
    capture_output=True, text=True
).stdout

# AI processes it
summary = your_ai_model.summarize(md)
```

### 6.3 LangChain / LlamaIndex Integration

```python
# Future AIDocLoader
from my_toolkit import AIDocLoader

loader = AIDocLoader("report.aidoc")
docs = loader.load()
# docs[0].page_content = raw Markdown text
```

### 6.4 Claude Code / Cursor Integration

Configure `.aidoc` files to route through `aidoc md`:

```json
{
  "extensions": {
    ".aidoc": {
      "read": "aidoc md {file}"
    }
  }
}
```

---

## 7. How It Differs from Plain ZIP

| Feature | Plain ZIP | AIDOC |
|---------|-----------|-------|
| Open with | Any ZIP tool | Any ZIP tool + AIDOC-aware tools |
| content.md | Optional | ✅ **Required, must be first entry** |
| AI read perf | Must parse Central Directory | 🚀 **Skips CD, 2.5× faster** |
| metadata.json | Optional | ✅ Required |
| Digital signing | None | ✅ PKCS#7 / SM2 |
| File extension | `.zip` | `.aidoc` |
| ZIP comment | Any | Fixed `AIDOCv1` |

**AIDOC IS a ZIP file.** This means:
- Any ZIP extractor can open it
- Any language's ZIP library can read/write it
- The "content.md first" convention benefits all ZIP implementations

---

## 8. FAQ

### Q: How much larger is an AIDOC file?

Typically only 1–2 KB overhead (metadata + signature). Negligible for Word/PDF documents.

### Q: How to verify AIDOC integrity?

```bash
aidoc verify file.aidoc
```

For unsigned files, you can compute SHA-256 manually.

### Q: Support batch processing?

```bash
# Batch pack
for f in *.md; do
    aidoc create "$f" -o "${f%.md}.aidoc" --author "Yu Shen"
done
```

### Q: Can I use it in CI/CD?

Yes. `aidoc verify` returns a non-zero exit code when verification fails, suitable for CI pipelines:

```yaml
# GitHub Actions
- name: Verify AIDOC
  run: aidoc verify report.aidoc
```

### Q: How does it compare to other formats?

| Format | Strength | Weakness |
|--------|----------|----------|
| ZIP | Universal | No semantics, no signing, not AI-friendly |
| PDF | Stable layout | AI parsing is painful, no signing |
| .docx | Rich editing | AI parsing overhead, large |
| **AIDOC** | **AI-friendly + signable + compatible** | New format needs toolchain support |

---

> **AIDOC** — Let AI and humans read the same file, each in their most comfortable way.
