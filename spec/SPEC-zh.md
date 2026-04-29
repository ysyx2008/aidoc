# AIDOC — AI 原生文档格式规范

> [English](SPEC.md) | **中文**

**版本**: 0.1.0（草案）  
**状态**: 提案标准  
**最后更新**: 2026-04-29

---

## 1. 概述

AIDOC（AI Document）是一种面向 AI 辅助文档阅读与处理时代设计的容器格式。它将人类可读的文档（Word、PDF、图片等）与 AI 优化的 Markdown 表示和结构化元数据打包在单一文件中。

### 1.1 设计目标

| 目标 | 说明 |
|------|------|
| **AI 优先** | AI 工具可直接读取 Markdown 内容，无需解析复杂二进制格式 |
| **人类兼容** | 原始文档完整保留，人类可使用标准软件直接打开 |
| **零依赖** | 以 ZIP 为容器——所有主流操作系统和语言原生支持 |
| **高效随机访问** | Markdown 内容不压缩存储，实现 O(1) 随机读取 |
| **自描述** | 包含元数据（标题、作者、标签、时间戳），便于索引和搜索 |

### 1.2 文件扩展名与 MIME 类型

- **扩展名**: `.aidoc`
- **MIME 类型**: `application/x-aidoc`（IANA 注册中）

---

## 2. 物理格式

### 2.1 容器

AIDOC **就是**一个标准 ZIP 文件。任何标准 ZIP 库都能在文件系统层面读取、创建和检查 AIDOC 文件。

```
┌──────────────────────────────────────┐
│            ZIP Container             │
│                                      │
│  ┌────────────────────────────────┐  │
│  │   content.md     (STORED)      │  │  ← 第 1 条目（AI 极速入口）
│  ├────────────────────────────────┤  │
│  │   metadata.json  (DEFLATED)    │  │
│  ├────────────────────────────────┤  │
│  │   document.docx  (STORED)      │  │  ← 原始文档
│  ├────────────────────────────────┤  │
│  │   ... (attachments)            │  │
│  └────────────────────────────────┘  │
│                                      │
│  ZIP Central Directory               │
│  ZIP End of Central Directory        │
│  Comment: "AIDOCv1"                  │
└──────────────────────────────────────┘
```

### 2.2 条目顺序

**⚠️ `content.md` 必须是 ZIP 容器中的第一个条目。** 这是 AIDOC 格式最重要的结构约定。它使 AI 极速读取算法成为可能（见 §4.1）——AI 工具可以跳过 ZIP 中央目录解析，直接定位到内容。

文件中不得有任何条目排在 `content.md` 之前。

### 2.3 魔数标识（文件识别）

ZIP 文件注释字段必须包含精确的字节序列 `AIDOCv1`（ASCII）。这使得工具无需解析整个 ZIP 结构即可快速验证文件是否为有效的 AIDOC 文档。

- **偏移量**: ZIP 文件末尾（EOCD 注释字段）
- **长度**: 6 字节
- **值**: `0x41 0x49 0x44 0x4F 0x43 0x76 0x31`（`AIDOCv1`）

### 2.4 压缩策略

| 条目 | 压缩方式 | 理由 |
|------|----------|------|
| `content.md` | `ZIP_STORED` (0) | AI 工具需要零开销直接读取；Markdown 本身很小 |
| `metadata.json` | `ZIP_DEFLATED` (8) | 小文件，压缩开销可忽略 |
| `document.*` | `ZIP_STORED` (0) | docx/xlsx/pptx 本身就是 ZIP 归档；pdf/jpg/png 已使用内部压缩 |
| 所有其他条目 | `ZIP_STORED` (0) | 除非创建者明确选择压缩 |

> **注意**: 对已压缩格式使用 `ZIP_STORED` 避免了"双重压缩"问题——对已压缩文件再次压缩只会带来极小的空间节省，代价是额外的 CPU 开销。

### 2.5 内部路径约定

容器内的所有路径都是**扁平**的（无子目录）。这保证了访问模式的简单和可预测。

| 保留名称 | 必需 | 说明 |
|----------|:----:|------|
| `content.md` | ✅ 是 | 机器可读的 Markdown 内容 |
| `metadata.json` | ✅ 是 | 结构化元数据 |
| `document.docx` | ⬜ 可选 | 原始 Word 文档 |
| `document.pdf` | ⬜ 可选 | 原始 PDF 文档 |
| 其他文件 | ⬜ 可选 | 附加附件 |

当捆绑多个原始文档时，命名遵循 `document.{ext}` 模式。对于同一类型的多个文档，使用索引名称：`document-1.docx`、`document-2.docx`。

---

## 3. 内部文件规范

### 3.1 `metadata.json`

元数据文件是一个 UTF-8 编码的 JSON 对象。每个有效的 AIDOC 文件中必须存在该文件。

**Schema:**

```jsonc
{
  // 必填字段
  "aidoc_version": "0.1.0",           // AIDOC 规范版本 (semver)
  "title": "文档标题",                  // 文档标题
  "created_at": "2026-04-29T08:30:00", // ISO 8601 创建时间戳

  // 可选字段
  "author": "于申",                     // 作者
  "tags": ["AI", "架构", "国元证券"],   // 分类标签
  "description": "文档摘要",            // 简要说明
  "source_url": "https://...",         // 原始来源 URL
  "original_format": "docx",           // 主要原始格式
  "ai_summary": "",                    // AI 生成的摘要（可由后续工具填充）
  "extensions": {}                     // 扩展特定元数据（见 §5）
}
```

### 3.2 `content.md`

Markdown 内容文件是 AI 的主要入口点。它必须以标准 Markdown 格式包含文档的全部文本内容。

**编码**: UTF-8（BOM 可选，推荐无 BOM 的 UTF-8）

**最小内容**: 至少包含一个一级标题作为文档标题：
```markdown
# 我的文档标题
```

**推荐实践:**
- 使用 ATX 标题（`#`、`##`、`###`）
- 使用 `>` 表示引用和标注
- 使用 `- [ ]`/`- [x]` 表示任务列表
- 使用 ``` 配合语言标签表示代码块
- 图片引用使用标准 Markdown `![alt](filename.jpg)` 格式，指向同一容器中的文件
- 不要在 Markdown 中嵌入 Base64 编码的二进制数据

**示例:**
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

## 4. 读取模式

### 4.1 AI 极速模式（主要）

由于 `content.md` 被保证是 ZIP 中的第一个条目，以 `ZIP_STORED`（无压缩）存储，且无数据描述符和额外字段，其数据位于固定偏移量。AI 可以**无需解析中央目录**直接读取：

```
1. 打开文件
2. 在偏移 0 处读取 30 字节的本地文件头
3. 验证：签名 == PK\x03\x04，方法 == STORED (0)，bit 3 == 0
4. 读取 filename_len（偏移 26，2 字节）+ extra_len（偏移 28，2 字节）
5. data_offset = 30 + filename_len + extra_len
6. 验证：偏移 30 处的文件名为 "content.md"
7. 读取 compressed_size（偏移 18，4 字节）
8. 定位到 data_offset，读取 compressed_size 字节
9. 解码为 UTF-8 → AI 直接处理
```

**总 I/O：1 次 seek + 2 次 read**（30 字节头部 + 数据）。  
**预期性能**: ~10–20μs/文件，相当于读取原始 `.md` 文件的性能。

**回退机制**: 如果极速模式失败（例如非标准 ZIP 变体），工具必须回退到基于中央目录的标准读取方式。

### 4.2 丰富模式（AI 带附件）

1. 执行 AI 极速模式步骤读取 `content.md`
2. 如果 AI 需要引用图片或原始文档：
   - 从 ZIP 中央目录读取 `metadata.json` 获取额外上下文
   - 按名称从 ZIP 中提取特定附件文件
3. 处理组合内容

### 4.3 人类模式

使用任何 ZIP 解压工具打开 `.aidoc` 文件，或使用支持 AIDOC 的工具提取原始文档，在标准软件中查看。

---

## 5. 扩展机制

### 5.1 元数据扩展

创建者可以向 `metadata.json` 的 `extensions` 对象添加自定义字段：

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

扩展键应使用反向域名表示法以避免冲突。

### 5.2 内容扩展

可以为特定用例向容器添加额外文件：

- `summary.md` — AI 生成的摘要（工具特定）
- `annotations.json` — 文档标注和高亮
- `embeddings.npy` — 向量嵌入（用于语义搜索）
- `changelog.md` — 版本历史

这些文件是可选的、工具特定的。工具必须优雅地忽略未知文件。

---

## 6. 数字签名

AIDOC 支持可选的数字签名，用于真实性验证和篡改检测。

### 6.1 签名后的文件结构

签名后，容器包含两个额外文件：

```
report.aidoc/
├── content.md              ← 第 1 条目（AI 极速读取不变）
├── metadata.json
├── document.docx
├── manifest.json           ← 所有文件的 SHA-256 哈希清单
└── signature.p7s           ← PKCS#7 分离签名
```

### 6.2 `manifest.json`

清单文件包含除自身和 `signature.p7s` 之外所有文件的 SHA-256 哈希值。

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

PKCS#7 (CMS) **分离签名**，DER 编码，作用于 `manifest.json` 的原始字节。

**支持的算法**：

| 算法 | 库 | 状态 |
|------|------|:----:|
| RSA-2048/SHA-256 | `cryptography` | ✅ 标准 |
| ECDSA P-256/SHA-256 | `cryptography` | ✅ 标准 |
| SM2/SM3 | `gmssl` | ✅ 可选 |

文件必须以 `ZIP_STORED`（不压缩）存储。

### 6.4 验证流程

```
┌─────────────┐      ┌─────────────┐      ┌──────────────────┐
│ signature   │ ───→ │ manifest    │ ───→ │ content.md       │
│ .p7s        │ 签名  │ .json       │ 哈希  │ metadata.json    │
│             │ 验证  │             │ 比对  │ document.docx    │
└─────────────┘      └─────────────┘      │ ...              │
                                           └──────────────────┘
```

步骤：
1. **PKCS#7 签名验证**: 验证 `signature.p7s` 是对 `manifest.json` 的有效 PKCS#7 分离签名。提取签名者证书信息。
2. **哈希比对**: 对 `manifest.json` 中列出的每个文件，计算 SHA-256 哈希并与记录值比对。
3. **结果**: 全部通过，文档方被视为真实且未被篡改。

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

## 7. 安全考虑

### 7.1 内容验证

- AIDOC 读取器必须验证 `content.md` 是有效的 UTF-8 文本
- AIDOC 读取器必须验证 `metadata.json` 是有效的 JSON
- 提取文件时，实现必须防范 ZIP 路径遍历攻击（例如包含 `../` 的文件名）

### 7.2 信任

- AIDOC 的签名机制提供了内置的防篡改和来源认证能力（见§6）
- 对于未签名的 AIDOC 文件，信任级别取决于文件来源渠道
- 签名证书本身的可信度由证书链和颁发机构决定

---

## 8. 版本与稳定性

AIDOC 使用两个独立的版本号来分离**规范的稳定性**和**工具的迭代速度**。

### 8.1 两层版本号

| 版本 | 范围 | 示例 | 变更频率 |
|------|------|------|----------|
| **规范版本** | `.aidoc` 文件格式本身（存于 `metadata.json`） | `0.1.0` | 极少——变更需正式提案 |
| **工具版本** | CLI 工具（`aidoc --version`） | `0.1.0` | 频繁——bug 修复、新功能 |

这意味着：
- 用工具 v0.5.0 创建、规范版本为 v1.0.0 的文件仍然有效
- 可以更新工具而不必担心破坏现有 AIDOC 文件
- 规范版本变更需要考虑迁移

### 8.2 规范版本生命周期

```
预发布 (v0.x) → 稳定 (v1.0.0) → 演进 (v1.x, v2.x)
```

**v0.x — 预发布**（当前）：
- 格式仍在稳定中
- 可能出现破坏性变更，但应有文档记录
- 反馈期：收集早期采用者的用例

**v1.0.0 — 首次稳定**：
- 格式冻结
- 所有现有 v1.x 读取器可读取所有 v1.x 文件
- 破坏性变更需要主版本升级（v2.0.0）
- 变更提案需经过评审流程

### 8.3 稳定性承诺

**对于规范 v1.0.0+：**

| 承诺 | 保证 |
|------|------|
| ✅ **前向兼容** | 按规范 v1.0 编写的文件符合所有 v1.x 读取器 |
| ✅ **后向兼容** | v1.1 读取器可读取所有 v1.0 文件 |
| ⚠️ **仅增量** | v1.x 变更仅添加新的可选字段；从不删除或重新解释现有字段 |
| 🚫 **破坏性变更** | 最低需要规范 v2.0.0；发布前至少提前 6 个月公告 |

**稳定性承诺不覆盖的内容：**
- 工具 CLI 接口（参数、输出格式）——由工具版本管理
- 性能特性
- 默认压缩设置

### 8.4 变更流程（规范 v1.0.0+）

对 AIDOC 规范的变更提案遵循以下流程：

```
1. 提案 → GitHub Issue 标记 "spec-change"
   - 描述变更
   - 解释动机和用例
   - 展示变更前后的示例

2. 讨论 → 2 周评审期
   - 社区反馈
   - 概念验证实现（可选但鼓励）

3. 决策 → 维护者达成共识
   - 接受 → 更新 SPEC.md，新版本/章节
   - 推迟 → 在未来的里程碑重新审视
   - 拒绝 → 附说明关闭

4. 发布 → 规范版本升级
   - 补丁 (0.0.x): 澄清说明、笔误修正
   - 次要 (0.x.0): 增量变更、新增可选特性
   - 主要 (x.0.0): 破坏性变更、格式重构
```

### 8.5 弃用政策

当某个特性被弃用时：
1. **弃用公告** — 更新规范，标记该特性为弃用
2. **宽限期** — 该特性至少继续工作 2 个小版本
3. **移除** — 仅在下一次主版本中发生

### 8.6 工具版本管理

CLI 工具遵循标准[语义化版本](https://semver.org/)：

- **补丁** (0.0.x): Bug 修复、文档改进
- **次要** (0.x.0): 新命令、新增可选特性（向后兼容）
- **主要** (x.0.0): CLI 破坏性变更

工具版本独立于规范版本。一个工具可以支持多个规范版本。

---

## 9. 示例

### 9.1 仅从 Markdown 创建

```
report.aidoc/
├── content.md          # Markdown 内容 (STORED)
└── metadata.json       # 元数据 (DEFLATED)
```

### 9.2 从 Word + Markdown + 附件创建

```
proposal.aidoc/
├── content.md          # Markdown 内容 (STORED)
├── document.docx       # 原始 Word 文档 (STORED)
├── figure-1.png        # 嵌入图片 (STORED)
├── figure-2.png        # 嵌入图片 (STORED)
└── metadata.json       # 元数据 (DEFLATED)
```

### 9.3 签名文档

```
report.aidoc/
├── content.md          # Markdown 内容 (STORED) ← 第 1 条目
├── document.docx       # 原始 Word 文档 (STORED)
├── metadata.json       # 元数据 (DEFLATED)
├── manifest.json       # 文件哈希清单 (DEFLATED)
└── signature.p7s       # PKCS#7 分离签名 (STORED)
```

签名命令：
```bash
aidoc sign report.aidoc --cert mycert.pem --key mykey.pem
```

### 9.4 从 PDF + 摘要 + 标签创建

```
report.aidoc/
├── content.md          # Markdown 内容 (STORED)
├── document.pdf        # 原始 PDF (STORED)
├── summary.md          # AI 生成的摘要 (STORED)
└── metadata.json       # 元数据 (DEFLATED)
```

---

## 10. 附录：实现检查清单

### 极速读取（AI 优化，跳过 ZIP 中央目录）

- [ ] 打开文件，在偏移 0 处读取 30 字节本地文件头
- [ ] 验证 `PK\x03\x04` 签名
- [ ] 验证压缩方式 == STORED (0)
- [ ] 验证 bit 3（数据描述符）== 0
- [ ] 读取 filename_len（偏移 26）和 extra_len（偏移 28）
- [ ] 验证偏移 30 处的文件名 == "content.md"
- [ ] 读取 compressed_size（偏移 18）
- [ ] 定位到 `30 + filename_len + extra_len`，读取 compressed_size 字节
- [ ] 解码为 UTF-8

### 标准读取（ZIP 中央目录）

- [ ] 读取 ZIP 中央目录
- [ ] 验证 `ZIP comment == "AIDOCv1"`
- [ ] 检查 `metadata.json` 存在且是有效的 JSON
- [ ] 检查 `content.md` 存在
- [ ] 验证 `aidoc_version` 的主版本兼容性
- [ ] 按名称提取单个文件（随机访问）
- [ ] 优雅处理未知/可选文件

### 签名

- [ ] 计算所有文件的 SHA-256 哈希（manifest.json 和 signature.p7s 除外）
- [ ] 构建包含算法、签署时间、文件哈希的 manifest.json
- [ ] 对 manifest.json 字节进行签名 → PKCS#7 分离签名 (DER)
- [ ] 将 manifest.json（DEFLATED）和 signature.p7s（STORED）加入容器
- [ ] 验证：签名有效 + 所有哈希匹配

### 验证

- [ ] 从容器的 manifest.json 和 signature.p7s
- [ ] 验证 PKCS#7 分离签名
- [ ] 提取签名者证书信息
- [ ] 重新计算所有文件的哈希并与 manifest 对比
- [ ] 安全：拒绝文件名中的路径遍历

---

## 11. 许可证

本项目（包括规范、源代码和文档）基于 [MIT 许可证](https://opensource.org/licenses/MIT) 发布。详见仓库根目录的 [LICENSE](../LICENSE) 文件。
