# AIDOC — AI-Native Document Format 使用指南

> **版本**: 0.1.0 · **更新**: 2026-04-29

---

## 目录

1. [概述](#1-概述)
2. [安装](#2-安装)
3. [快速上手](#3-快速上手)
4. [命令参考](#4-命令参考)
5. [数字签名](#5-数字签名)
6. [AI 工具链集成](#6-ai-工具链集成)
7. [与普通 ZIP 的区别](#7-与普通-zip-的区别)
8. [常见问题](#8-常见问题)

---

## 1. 概述

### 1.1 什么是 AIDOC？

AIDOC（AI Document）是一种 **AI 原生文档容器格式**。它将「给人看的原始文档」和「给 AI 读的 Markdown」打包在同一个 ZIP 文件中，让 AI 和人类用各自最舒服的方式处理同一份文档。

```
report.aidoc/
├── content.md          ← 🚀 AI 直接读取（STORED，第 1 条目）
├── metadata.json       ← 📋 结构化元数据
├── document.docx       ← 📄 原始 Word 文档
└── 封面.png            ← 🖼️ 附件图片
```

### 1.2 核心设计原理

| 原理 | 说明 |
|------|------|
| **content.md 排第一** | 始终是 ZIP 第一个条目，AI 读取无需解析中央目录 |
| **STORED 不压缩** | Markdown 文本很轻，不压缩换来零开销读取 |
| **纯标准 ZIP** | 不魔改 ZIP 结构，任何 ZIP 工具都能打开 |
| **可数字签名** | 支持 PKCS#7 / 国密 SM2，确保文件来源可信 |

### 1.3 适用场景

- **AI 研报生成** → 输出 .aidoc，AI 读 MD 写摘要，人类用 Word 看原文
- **文档归档** → 一份文件同时存原文和 AI 摘要
- **金融合规** → 签名保证文档不被篡改，审计可溯源
- **知识库管理** → AI 索引直接读 MD，无需解析 PDF/Word

---

## 2. 安装

### 方式一：直接使用

```bash
git clone https://github.com/你的用户名/aidoc.git ~/Source/aidoc
export PATH="$HOME/Source/aidoc/bin:$PATH"
```

### 方式二：pip 安装

```bash
cd ~/Source/aidoc/src
pip install .
aidoc --version
```

### 依赖说明

| 功能 | 依赖 | 安装方式 |
|------|------|----------|
| 核心功能（打包/读取/提取） | 无（纯标准库） | 开箱即用 |
| 数字签名（RSA/ECDSA） | openssl（系统自带） | 开箱即用 |
| 生成测试证书 | `cryptography` | `pip install cryptography` |
| 国密 SM2 签名 | `gmssl` | `pip install gmssl` |

---

## 3. 快速上手

### 3.1 从 Markdown 创建 AIDOC

```bash
# 创建一个 Markdown 文件
cat > mydoc.md << 'EOF'
# 我的文档

这是我的第一个 AIDOC 文档。

## 章节一

一些内容...
EOF

# 打包为 .aidoc
aidoc create mydoc.md -o mydoc.aidoc --author "于申" --tags "AI,文档"
```

### 3.2 AI 读取内容

```bash
# 🚀 极速读取模式
aidoc md mydoc.aidoc
```

### 3.3 查看元数据和文件清单

```bash
# 查看元数据
aidoc meta mydoc.aidoc

# 列出所有文件
aidoc ls mydoc.aidoc
```

### 3.4 提取原始文件

```bash
# 提取所有文件到 output 目录
aidoc extract mydoc.aidoc ./output
```

### 3.5 更多创建方式

```bash
# 创建空白模板
aidoc init -o template.aidoc --title "模板文档"

# 打包 Word + 图片
aidoc create report.docx figure1.png -o report.aidoc

# 打包 Word + Markdown 摘要 + 封面图片
aidoc create report.docx summary.md cover.png -o report.aidoc
```

---

## 4. 命令参考

### 4.1 `aidoc init`

从模板创建空白 AIDOC 文件。

```bash
aidoc init [-o OUTPUT] [--title TITLE]
```

**参数**:
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-o` | 输出路径 | `untitled.aidoc` |
| `--title` | 文档标题 | `Untitled` |

### 4.2 `aidoc create`

将文件打包为 AIDOC。

```bash
aidoc create <文件...> [-o OUTPUT] [--title TITLE] [--author AUTHOR] [--tags TAGS]
```

**参数**:
| 参数 | 说明 |
|------|------|
| `<文件...>` | 一个或多个文件。.md/.markdown 自动识别为 Markdown；.docx/.doc/.pdf 等自动识别为原始文档；其余作为附件 |
| `-o` | 输出路径（默认根据标题自动生成） |
| `--title` | 文档标题（默认从文件名推断） |
| `--author` | 作者 |
| `--tags` | 逗号分隔的标签 |

**文件分类规则**:
| 扩展名 | 分类 | 存储方式 |
|--------|------|----------|
| `.md`, `.markdown` | Markdown 内容 | `content.md` / STORED |
| `.docx`, `.doc`, `.pdf`, `.xlsx`, `.xls`, `.pptx` | 原始文档 | `document.{ext}` / STORED |
| 其他（.jpg, .png, .zip 等） | 附件 | 原文件名 / STORED |

### 4.3 `aidoc md`

读取 AIDOC 中的 Markdown 内容（AI 专用模式）。

```bash
aidoc md <file.aidoc>
```

**特点**:
- 🚀 优先使用**极速模式**，跳过 ZIP 中央目录
- 📉 单次读取约 **10μs**（见性能报告）
- 极速模式失败时自动降级到标准 ZIP 读取

### 4.4 `aidoc ls`

列出容器内所有文件及其压缩信息。

```bash
aidoc ls <file.aidoc>
```

输出示例：
```
  名称                             原始大小     实际大小 方式
  ────────────────────────────── ────────── ────────── ────────
  content.md                          1,117 B      1,117 B STORED
  metadata.json                         164 B        123 B DEFLATED
  manifest.json                         230 B        186 B DEFLATED
  signature.p7s                      1,316 B      1,316 B STORED
  ────────────────────────────── ────────── ────────── ────────
  合计                                2,827 B      2,742 B  压缩比: 97.0%
```

### 4.5 `aidoc meta`

查看元数据。

```bash
aidoc meta <file.aidoc>
```

### 4.6 `aidoc info`

查看元数据 + 文件清单（meta + ls 的组合）。

```bash
aidoc info <file.aidoc>
```

### 4.7 `aidoc check`

检查文件是否为有效的 AIDOC 格式。

```bash
aidoc check <file.aidoc>
```

### 4.8 `aidoc extract`

提取容器中的所有文件。

```bash
aidoc extract <file.aidoc> [output_dir]
```

---

## 5. 数字签名

### 5.1 签名

```bash
# 生成测试证书并签名（开发测试用）
aidoc sign report.aidoc --gen-key

# 用企业 CA 证书签名
aidoc sign report.aidoc --cert mycert.pem --key mykey.pem

# 国密 SM2 签名
aidoc sign report.aidoc --cert sm2.pem --key sm2.pem --sm2
```

### 5.2 验证

```bash
aidoc verify report.aidoc
```

输出示例：
```
  ✅ 签名有效 — 文件完整，未被篡改
    签署者: CN=AIDOC Test Cert, O=AIDOC
    颁发者: CN=AIDOC Test Cert, O=AIDOC
    有效期: Apr 29 2026 — Apr 29 2027
    算法:   sm3
    签署于: 2026-04-29T09:15:22
```

如果文件被篡改：
```
  ❌ 文件已被篡改!
    原因: Verification failure
```

### 5.3 验证算法

| 算法 | 命令 | 依赖 |
|------|------|------|
| RSA-2048/SHA-256 | `aidoc sign --cert c.pem --key k.pem` | openssl |
| ECDSA P-256/SHA-256 | `aidoc sign --cert c.pem --key k.pem` | openssl |
| SM2/SM3 | `aidoc sign --cert c.pem --key k.pem --sm2` | openssl + gmssl |

---

## 6. AI 工具链集成

### 6.1 极速读取原理

AIDOC 的核心优化：**content.md 是 ZIP 中的第一个条目**，STORED 存储，无 data descriptor，无 extra field。

因此数据偏移固定为 40 字节，AI 只需：

```python
def read_md_fast(path):
    with open(path, 'rb') as f:
        header = f.read(30)                 # 读取 local file header
        fn_len = int.from_bytes(header[26:28], 'little')
        ext_len = int.from_bytes(header[28:30], 'little')
        data_offset = 30 + fn_len + ext_len  # 计算数据偏移
        data_size = int.from_bytes(header[18:22], 'little')
        f.seek(data_offset)                  # 直接定位
        return f.read(data_size).decode('utf-8')
```

**性能**：约 **10.8μs/次**，比标准 ZIP 读取快 **2.5 倍**。

### 6.2 Python 集成示例

```python
import subprocess

# 读取 MD 内容
md = subprocess.run(
    ['aidoc', 'md', 'report.aidoc'],
    capture_output=True, text=True
).stdout

# AI 处理
summary = your_ai_model.summarize(md)
```

### 6.3 与 LangChain 集成

```python
from langchain.document_loaders import AIDocLoader  # 未来

loader = AIDocLoader("report.aidoc")
docs = loader.load()
# docs[0].page_content = content.md 的文本内容
```

### 6.4 与 Claude Code / Cursor 等工具集成

在工具配置中将 `.aidoc` 文件的读取命令指向 `aidoc md`：

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

## 7. 与普通 ZIP 的区别

| 特性 | 普通 ZIP | AIDOC |
|------|----------|-------|
| 打开方式 | 任意 ZIP 工具 | 任意 ZIP 工具 + AIDOC 专用工具 |
| content.md | 可选 | ✅ **必须存在且排第一** |
| AI 读取性能 | 需解析中央目录 | 🚀 **跳过中央目录，快 2.5 倍** |
| metadata.json | 可选 | ✅ 必须存在 |
| 数字签名 | 无 | ✅ PKCS#7 / SM2 |
| 文件扩展名 | `.zip` | `.aidoc` |
| ZIP comment | 无关 | 固定 `AIDOCv1` |

**AIDOC 本质上就是 ZIP**。这意味着：
- 任何 ZIP 解压工具都能打开 AIDOC 文件
- 任何语言的 ZIP 库都能读写 AIDOC 文件（不一定要用 AIDOC 专用工具）
- content.md 排第一的约定对所有 ZIP 实现都有效

---

## 8. 常见问题

### Q: AIDOC 文件比原文件大多少？

通常只大 1-2 KB（元数据 + 签名）。对于 Word/PDF 文档来说可以忽略不计。

### Q: 如何验证 AIDOC 文件的完整性？

```bash
aidoc verify file.aidoc
```

未签名的文件可以通过 SHA-256 自行验证。

### Q: 支持批量处理吗？

```bash
# 批量打包
for f in *.md; do
    aidoc create "$f" -o "${f%.md}.aidoc" --author "于申"
done
```

### Q: 可以在 CI/CD 中使用吗？

可以。验证命令返回非零退出码（签名无效或文件被篡改时），适合 CI 流程：

```yaml
# GitHub Actions 示例
- name: Verify AIDOC
  run: aidoc verify report.aidoc
```

### Q: 和其他格式比怎么样？

| 格式 | 优势 | 劣势 |
|------|------|------|
| ZIP | 通用 | 无语义、无签名、AI 不友好 |
| PDF | 排版稳定 | AI 解析困难、不可签名 |
| .docx | 丰富编辑 | AI 解析损耗大、大文件 |
| **AIDOC** | **AI 友好 + 可签名 + 兼容** | 新格式需工具链支持 |

---

> **AIDOC** — 让 AI 和人类读同一份文件，但用各自最舒服的方式。
