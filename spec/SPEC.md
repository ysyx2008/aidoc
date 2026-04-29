# AIDOC — AI-Native Document Format Specification

> **English** | [中文](SPEC-zh.md)

**Version**: 0.1.0 (Draft)  
**Status**: Proposed Standard  
**Last Updated**: 2026-04-29

---

## 1. Overview

AIDOC (AI Document) is a container format designed for the age of AI-assisted document reading and processing. It bundles human-readable documents (Word, PDF, images, etc.) with an AI-optimized Markdown representation and structured metadata in a single file.

### 1.1 Design Goals

| Goal | Description |
|------|-------------|
| **AI-First** | AI tools can read the Markdown content instantly without parsing complex binary formats |
| **Human-Compatible** | Original documents remain intact for human readers using standard software |
| **Zero Dependency** | Uses ZIP as the container — natively supported by all major operating systems and languages |
| **Efficient Random Access** | Markdown content is stored uncompressed for O(1) random read |
| **Self-Describing** | Contains metadata (title, author, tags, timestamps) for indexing and search |

### 1.2 File Extension & MIME Type

- **Extension**: `.aidoc`
- **MIME Type**: `application/x-aidoc` (pending IANA registration)

---

## 2. Physical Format

### 2.1 Container

AIDOC **IS** a standard ZIP file. Any standard ZIP library can read, create, and inspect AIDOC files at the filesystem level.

```
┌──────────────────────────────────────┐
│            ZIP Container             │
│                                      │
│  ┌────────────────────────────────┐  │
│  │   content.md     (STORED)      │  │  ← 第 1 条目（AI 极速入口）
│  ├────────────────────────────────┤  │
│  │   metadata.json  (DEFLATED)    │  │
│  ├────────────────────────────────┤  │
│  │   document.docx  (STORED)      │  │  ← Original document
│  ├────────────────────────────────┤  │
│  │   ... (attachments)            │  │
│  └────────────────────────────────┘  │
│                                      │
│  ZIP Central Directory               │
│  ZIP End of Central Directory        │
│  Comment: "AIDOCv1"                  │
└──────────────────────────────────────┘
```

### 2.2 Entry Order

**⚠️ `content.md` MUST be the first entry in the ZIP container.** This is the most important structural convention of the AIDOC format. It enables the AI Fast Read algorithm (see §4.1) — AI tools can skip ZIP central directory parsing and seek directly to the content.

No other entries may precede `content.md` in the file.

### 2.3 Magic Bytes (File Identification)

The ZIP file comment field MUST contain the exact byte sequence `AIDOCv1` (ASCII). This allows tools to quickly verify whether a file is a valid AIDOC document without parsing the full ZIP structure.

- **Offset**: End of the ZIP file (in the EOCD comment field)
- **Length**: 6 bytes
- **Value**: `0x41 0x49 0x44 0x4F 0x43 0x76 0x31` (`AIDOCv1`)

### 2.4 Compression Strategy

| Entry | Compression | Rationale |
|-------|-------------|-----------|
| `content.md` | `ZIP_STORED` (0) | AI tools need zero-overhead direct reading; Markdown is small already |
| `metadata.json` | `ZIP_DEFLATED` (8) | Small file, compression overhead is negligible |
| `document.*` | `ZIP_STORED` (0) | docx/xlsx/pptx are already ZIP archives; pdf/jpg/png already use internal compression |
| All other entries | `ZIP_STORED` (0) | Unless the creator explicitly opts for compression |

> **Note**: Using `ZIP_STORED` for already-compressed formats avoids the "double compression" problem — compressing a compressed file yields negligible space savings at the cost of CPU time.

### 2.5 Internal Path Convention

All paths within the container are **flat** (no subdirectories). This keeps access patterns simple and predictable.

| Reserved Name | Required | Description |
|---------------|----------|-------------|
| `content.md` | ✅ Yes | Machine-readable Markdown content |
| `metadata.json` | ✅ Yes | Structured metadata |
| `document.docx` | ⬜ Optional | Original Word document |
| `document.pdf` | ⬜ Optional | Original PDF document |
| Other files | ⬜ Optional | Additional attachments |

When bundling multiple original documents, naming follows the pattern `document.{ext}`. For multiple documents of the same type, use indexed names: `document-1.docx`, `document-2.docx`.

---

## 3. Internal File Specifications

### 3.1 `metadata.json`

The metadata file is a UTF-8 encoded JSON object. It MUST exist in every valid AIDOC file.

**Schema:**

```jsonc
{
  // REQUIRED fields
  "aidoc_version": "0.1.0",       // AIDOC spec version (semver)
  "title": "文档标题",              // Document title
  "created_at": "2026-04-29T08:30:00",  // ISO 8601 creation timestamp

  // OPTIONAL fields
  "author": "于申",                // Author name(s)
  "tags": ["AI", "架构", "国元证券"],  // Tags for categorization
  "description": "文档摘要",        // Brief description
  "source_url": "https://...",     // Original source URL
  "original_format": "docx",       // Primary original format
  "ai_summary": "",                // AI-generated summary (may be populated later)
  "extensions": {}                 // Extension-specific metadata (see §5)
}
```

### 3.2 `content.md`

The Markdown content file is the AI's primary entry point. It MUST contain the full textual content of the document in standard Markdown format.

**Encoding**: UTF-8 (BOM optional, UTF-8 without BOM preferred)

**Minimum content**: At minimum, a level-1 heading with the document title:
```markdown
# My Document Title
```

**Recommended practices:**
- Use ATX headings (`#`, `##`, `###`)
- Use `>` for blockquotes and callouts
- Use `- [ ]`/`- [x]` for checklists
- Use ``` for code blocks with language tags
- Include image references as standard Markdown `![alt](filename.jpg)` format pointing to files in the same container
- Do NOT include binary data as base64 in the Markdown

**Example:**
```markdown
# 人工智能六层架构分析报告

> 作者：于申 | 日期：2026-04-28

## 一、基础设施层

当前已完成 GPU 集群搭建，共部署 8 张 A100 显卡。

## 二、数据层

数据湖已接入行情、研报、公告三大数据源。

![数据湖架构图](data-lake-architecture.png)
```

---

## 4. Reading Modes

### 4.1 AI-Fast Mode (Primary)

Since `content.md` is guaranteed to be the first entry in the ZIP, stored with `ZIP_STORED` (no compression), and with no data descriptor or extra fields, its data is at a fixed offset. The AI can read it **without parsing the Central Directory**:

```
1. Open file
2. Read 30-byte local file header at offset 0
3. Verify: signature == PK\x03\x04, method == STORED (0), bit 3 == 0
4. Read filename_len (offset 26, 2 bytes) + extra_len (offset 28, 2 bytes)
5. data_offset = 30 + filename_len + extra_len
6. Verify: filename at offset 30 == "content.md"
7. Read compressed_size (offset 18, 4 bytes)
8. Seek to data_offset, read compressed_size bytes
9. Decode as UTF-8 → AI processes directly
```

**Total I/O: 1 seek + 2 reads** (header 30B + data).  
**Expected performance**: ~10–20μs per file, comparable to reading a raw `.md` file on disk.

**Fallback**: If the fast path fails (e.g., non-standard ZIP variant), tools MUST fall back to the standard Central Directory-based read.

### 4.2 Rich Mode (AI with attachments)

1. Perform AI-Fast Mode steps to read `content.md`
2. If the AI needs to reference images or original documents:
   - Read `metadata.json` from the ZIP Central Directory for additional context
   - Extract specific attachment files by name from the ZIP
3. Process combined content

### 4.3 Human Mode

Open the `.aidoc` file with any ZIP extractor, or use an AIDOC-aware tool to extract the original document(s) for viewing in standard software.

---

## 5. Extension Mechanism

### 5.1 Metadata Extensions

Creators can add custom fields to `metadata.json`'s `extensions` object:

```json
{
  "extensions": {
    "com.example.myapp": {
      "custom_field": "value",
      "version": 1
    }
  }
}
```

Extension keys SHOULD use reverse domain name notation to avoid collisions.

### 5.2 Content Extensions

Additional files can be added to the container for specialized use cases:

- `summary.md` — AI-generated summary (tool-specific)
- `annotations.json` — Document annotations and highlights
- `embeddings.npy` — Vector embeddings for semantic search
- `changelog.md` — Version history

These files are optional and tool-specific. Tools MUST gracefully ignore unknown files.

---

## 6. Digital Signing (数字证书签名)

AIDOC supports optional digital signing for authenticity verification and tamper detection.

### 6.1 Signed File Structure

When signed, the container contains two additional files:

```
report.aidoc/
├── content.md              ← 第 1 条目（AI 极速读取不变）
├── metadata.json
├── document.docx
├── manifest.json           ← 所有文件的 SHA-256 哈希清单（NEW）
└── signature.p7s           ← PKCS#7 分离签名（NEW）
```

### 6.2 `manifest.json`

The manifest file contains SHA-256 hashes of all files **except** itself and `signature.p7s`.

```json
{
  "aidoc_version": "0.1.0",
  "manifest_version": "1.0",
  "algorithm": "sha256",
  "signed_at": "2026-04-29T09:00:00",
  "files": {
    "content.md": {
      "sha256": "e3b0c44298fc1c149afbf4c8996fb924...",
      "size": 1117
    },
    "metadata.json": {
      "sha256": "d7a8fbb307d7809469ca9abcb0082e4f...",
      "size": 164
    }
  }
}
```

**设计原则**：
- `manifest.json` 不包含自身哈希（数学上不可能，见 §6.4）
- `signature.p7s` 不包含在 manifest 中（它是 manifest 的签名者，不是被验证对象）
- manifest 被签名后不可篡改，从而链式保证了所有文件的完整性

### 6.3 `signature.p7s`

A PKCS#7 (CMS) **detached signature** in DER encoding, over the raw bytes of `manifest.json`.

**支持的算法**：

| Algorithm | Library | Status |
|-----------|---------|--------|
| RSA-2048/SHA-256 | `cryptography` | ✅ Standard |
| ECDSA P-256/SHA-256 | `cryptography` | ✅ Standard |
| SM2/SM3 | `gmssl` | ✅ Optional |

File MUST be stored with `ZIP_STORED` (no compression).

### 6.4 Verification Process

```
┌─────────────┐      ┌─────────────┐      ┌──────────────────┐
│ signature   │ ───→ │ manifest    │ ───→ │ content.md       │
│ .p7s        │ 签名  │ .json       │ 哈希  │ metadata.json    │
│             │ 验证  │             │ 比对  │ document.docx    │
└─────────────┘      └─────────────┘      │ ...              │
                                           └──────────────────┘
```

Steps:
1. **PKCS#7 签名验证**: Verify that `signature.p7s` is a valid PKCS#7 detached signature of `manifest.json`. Extract signer certificate info.
2. **哈希比对**: For each file listed in `manifest.json`, compute SHA-256 hash and compare with the recorded value.
3. **结果**: All must pass for the document to be considered authentic and untampered.

### 6.5 `manifest.json` 为什么不包含自身哈希？

这是哈希完整性校验的经典设计。manifest 的完整性由 signature.p7s 保证（PKCS#7 签名保护了 manifest 的内容不被篡改），不需要自身哈希。

如果尝试包含自身哈希：
- 要计算 manifest 的哈希，需要先有完整的 manifest 内容
- 而 manifest 内容里又包含了自身的哈希值
- 这就形成了循环依赖，数学上不可解

### 6.6 `signature.p7s` 为什么不包含在 manifest 中？

`signature.p7s` 是外部验证者，不是被验证对象。验证流程是：

```
signature.p7s 验证 manifest.json → manifest.json 保证所有其他文件
```

`signature.p7s` 的内容是 PKCS#7 签名数据，验证时由工具按文件约定名称 `signature.p7s` 自动查找，无需 manifest 指向。

### 6.7 签名不影响 AI 极速读取

签名相关文件（manifest.json, signature.p7s）添加在 content.md 之后，content.md 始终是第一个 ZIP 条目，AI 极速读取路径不受任何影响。

---

## 7. Security Considerations

### 7.1 Content Validation

- AIDOC readers MUST validate that `content.md` is valid UTF-8 text
- AIDOC readers MUST validate that `metadata.json` is valid JSON
- When extracting files, implementations MUST guard against ZIP path traversal attacks (e.g., filenames containing `../`)

### 7.2 Trust

- AIDOC 的签名机制提供了内置的防篡改和来源认证能力（见§6）
- 对于未签名的 AIDOC 文件，信任级别取决于文件来源渠道
- 签名证书本身的可信度由证书链和颁发机构决定

---

## 8. Versioning & Stability

AIDOC uses two independent version numbers to separate **specification stability** from **tool iteration speed**.

### 8.1 Two-Level Versioning

| Version | Scope | Example | Change Frequency |
|---------|-------|---------|-----------------|
| **Spec Version** | The `.aidoc` file format itself (stored in `metadata.json`) | `0.1.0` | Rare — changes require formal proposal |
| **Tool Version** | The CLI tool (`aidoc --version`) | `0.1.0` | Frequent — bug fixes, new features |

This separation means:
- A file created by tool v0.5.0 with spec v1.0.0 is still valid
- You can update the tool without worrying about breaking existing AIDOC files
- Spec version changes require migration considerations

### 8.2 Spec Version Lifecycle

```
Pre-release (v0.x) → Stable (v1.0.0) → Evolution (v1.x, v2.x)
```

**v0.x — Pre-release** (current):
- Format is still being stabilized
- Breaking changes possible but should be documented
- Feedback period: gather use cases from early adopters

**v1.0.0 — First Stable**:
- Format is frozen
- All existing v1.x readers can read all v1.x files
- Breaking changes require a major version bump (v2.0.0)
- Change proposals go through review process

### 8.3 Stability Promises

**For Spec v1.0.0+:**

| Promise | Guarantee |
|---------|-----------|
| ✅ **Forward compatibility** | A file written with spec v1.0 conforms to all v1.x readers |
| ✅ **Backward compatibility** | A v1.1 reader can read all v1.0 files |
| ⚠️ **Additive only** | v1.x changes only add new optional fields; never remove or reinterpret existing fields |
| 🚫 **Breaking changes** | Require spec v2.0.0 minimum; announced at least 6 months before release |

**What is NOT covered by stability promise:**
- Tool CLI interface (flags, output format) — tool version governs this
- Performance characteristics
- Default compression settings

### 8.4 Change Process (for Spec v1.0.0+)

Proposed changes to the AIDOC specification follow this process:

```
1. Proposal → GitHub Issue with "spec-change" label
   - Describe the change
   - Explain motivation and use cases
   - Show before/after examples

2. Discussion → 2-week review period
   - Community feedback
   - Implementation proof-of-concept (optional but encouraged)

3. Decision → Maintainer consensus
   - Accepted → Update SPEC.md with new section/version
   - Deferred → Revisit in future milestone
   - Rejected → Close with explanation

4. Release → Spec version bump
   - Patch (0.0.x): Clarifications, typo fixes
   - Minor (0.x.0): Additive changes, new optional features
   - Major (x.0.0): Breaking changes, format restructuring
```

### 8.5 Deprecation Policy

When a feature is deprecated:
1. **Deprecation announced** — Spec is updated, feature marked as deprecated
2. **Grace period** — Feature still works for at least 2 minor versions
3. **Removal** — Only happens in the next major version

### 8.6 Tool Versioning

The CLI tool follows standard [Semantic Versioning](https://semver.org/):

- **Patch** (0.0.x): Bug fixes, documentation improvements
- **Minor** (0.x.0): New commands, new optional features (backward compatible)
- **Major** (x.0.0): Breaking CLI changes

The tool version is independent of the spec version. A tool may support multiple spec versions.

---

## 9. Example

### 9.1 Creating from Markdown only

```
report.aidoc/
├── content.md          # Markdown content (STORED)
└── metadata.json       # Metadata (DEFLATED)
```

### 9.2 Creating from Word + Markdown + Attachments

```
proposal.aidoc/
├── content.md          # Markdown content (STORED)
├── document.docx       # Original Word document (STORED)
├── figure-1.png        # Embedded figure (STORED)
├── figure-2.png        # Embedded figure (STORED)
└── metadata.json       # Metadata (DEFLATED)
```

### 9.3 Signed document with PKCS#7

```
report.aidoc/
├── content.md          # Markdown content (STORED) ← 第1条目
├── document.docx       # Original Word document (STORED)
├── metadata.json       # Metadata (DEFLATED)
├── manifest.json       # File hash manifest (DEFLATED)
└── signature.p7s       # PKCS#7 detached signature (STORED)
```

Signature added via:
```bash
aidoc sign report.aidoc --cert mycert.pem --key mykey.pem
```

### 9.4 Creating from PDF + Summary + Tags

```
report.aidoc/
├── content.md          # Markdown content (STORED)
├── document.pdf        # Original PDF (STORED)
├── summary.md          # AI-generated summary (STORED)
└── metadata.json       # Metadata (DEFLATED)
```

---

## 10. Appendix: Implementation Checklist

For developers implementing AIDOC support:

**Fast Read (AI-Optimized, skip ZIP central directory):**
- [ ] Open file, read 30-byte local file header at offset 0
- [ ] Verify `PK\x03\x04` signature
- [ ] Verify compression method == STORED (0)
- [ ] Verify bit 3 (data descriptor) == 0
- [ ] Read filename_len (offset 26) and extra_len (offset 28)
- [ ] Verify filename at offset 30 == "content.md"
- [ ] Read compressed_size (offset 18)
- [ ] Seek to `30 + filename_len + extra_len`, read compressed_size bytes
- [ ] Decode as UTF-8

**Standard Read (ZIP Central Directory):**
- [ ] Read ZIP central directory
- [ ] Validate `ZIP comment == "AIDOCv1"`
- [ ] Check `metadata.json` exists and is valid JSON
- [ ] Check `content.md` exists
- [ ] Validate `aidoc_version` MAJOR compatibility
- [ ] Extract single file by name (random access)
- [ ] Gracefully handle unknown/optional files

**Signing:**
- [ ] Compute SHA-256 for all files (except manifest.json and signature.p7s)
- [ ] Build manifest.json with algorithm, signed_at, file hashes
- [ ] Sign manifest.json bytes → PKCS#7 detached signature (DER)
- [ ] Add manifest.json (DEFLATED) and signature.p7s (STORED) to container
- [ ] Verify: signature valid + all hashes match

**Verification:**
- [ ] Read manifest.json and signature.p7s from container
- [ ] Verify PKCS#7 detached signature against manifest.json
- [ ] Extract signer certificate info
- [ ] Recompute hashes for all files and compare with manifest
- [ ] Security: reject path traversal in filenames

---

## 11. License

This project (including specification, source code, and documentation) is published under the [MIT License](https://opensource.org/licenses/MIT). See the [LICENSE](../LICENSE) file in the repository root for details.
