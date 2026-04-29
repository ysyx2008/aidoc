<p align="center">
  <img src="docs/logo.svg" width="120" alt="AIDOC Logo" />
</p>

<h1 align="center">AIDOC — AI-Native Document Format</h1>

<p align="center">
  <em>给 AI 一份它读得懂的文档，给人一份他看得见的文档。</em>
</p>

<p align="center">
  <a href="docs/guide-zh.md">📖 中文指南</a> ·
  <a href="docs/guide-en.md">📖 English Guide</a> ·
  <a href="docs/performance-zh.md">📊 性能报告</a> ·
  <a href="docs/performance-en.md">📊 Benchmark</a> ·
  <a href="spec/SPEC.md">📐 规范 (EN)</a> ·
  <a href="spec/SPEC-zh.md">📐 规范 (中文)</a> ·
  <a href="examples/">📁 示例</a>
</p>

<p align="center">
  <a href="#quick-start">🚀 快速开始</a> ·
  <a href="#core-features">✨ 核心特性</a> ·
  <a href="#why-aidoc">💡 为什么</a> ·
  <a href="#roadmap">🗺️ 路线图</a>
</p>

---

## 为什么需要 AIDOC？

**现状**：AI 读 Word、PDF 就像隔着毛玻璃——解析排版、表格、图片总有损耗。但 Markdown 对 AI 来说是母语。

**AIDOC 的解决方案**：把「给人看的原始文档」和「给 AI 读的 Markdown」打包在一个容器里，各取所需。

```
┌───────────────────────────┐
│       report.aidoc        │
│                           │
│  📝 content.md   [STORED] │ ← AI 直接读取，零开销
│  📄 document.docx [STORED]│ ← 人类用 Word 打开
│  🖼️  figure.png   [STORED]│ ← 附件图片
│  📋 metadata.json         │ ← 结构化元数据
└───────────────────────────┘
```

## 📚 文档

| 文档 | 语言 | 说明 |
|:----|:----:|:----|
| [📖 中文使用指南](docs/guide-zh.md) | 🇨🇳 中文 | 从安装到签名，覆盖所有命令和场景 |
| [📖 English User Guide](docs/guide-en.md) | 🇬🇧 English | Installation, commands, signing & AI integration |
| [📊 性能测试报告](docs/performance-zh.md) | 🇨🇳 中文 | 极速读取实测数据：2.9x 加速对比 |
| [📊 Performance Benchmark](docs/performance-en.md) | 🇬🇧 English | Benchmark: 2.9x speedup vs standard ZIP |
| [📐 格式规范 (SPEC)](spec/SPEC.md) | 🇨🇳 中文 | 文件格式的完整技术规范 |
| [📁 示例](examples/) | — | 示例文件和用法 |

## 核心特性

| 特性 | 说明 |
|------|------|
| 🚀 **AI-优先** | content.md 排第一 + STORED 存储，跳过中央目录，1 次 seek 极速读取 |
| 📄 **人类友好** | 原始文档（Word/PDF）完整保留，标准软件可直接打开 |
| 🎒 **零依赖** | 本质是 ZIP 文件，所有语言原生支持 |
| 🔍 **自描述** | 内置元数据（标题、作者、标签、时间戳） |
| 🧩 **可扩展** | 支持自定义元数据和附件文件 |

## 快速开始

### 安装

```bash
# 方式一：直接使用（无需安装）
cd ~/Source/aidoc
./bin/aidoc --help

# 方式二：pip 安装
cd src && pip install .
```

### 用法

```bash
# 创建空白容器
aidoc init -o 笔记.aidoc --title '我的笔记'

# Markdown → AIDOC
aidoc create 报告.md -o 报告.aidoc --author '旗鱼' --tags 'AI,架构'

# Word + Markdown → AIDOC
aidoc create 文档.docx 摘要.md 封面.png -o 文档.aidoc

# 数字签名（可选）
aidoc sign 报告.aidoc --gen-key           # 生成测试证书并签名
aidoc sign 报告.aidoc --cert cert.pem --key key.pem  # 用企业证书签名
aidoc verify 报告.aidoc                    # 验证签名

# AI 快速读取 Markdown（核心场景）
aidoc md 报告.aidoc

# 查看元数据
aidoc meta 报告.aidoc

# 列出容器内文件
aidoc ls 报告.aidoc

# 提取原始文件
aidoc extract 报告.aidoc ./导出
```

### AI 工具链集成示例

```python
import subprocess

# AI 读取 AIDOC 内容（毫秒级）
md_content = subprocess.run(
    ['aidoc', 'md', 'report.aidoc'],
    capture_output=True, text=True
).stdout

# AI 直接处理 Markdown
# ... your AI processing logic ...
```

## 规范文档

详细的文件格式规范请参阅 [spec/SPEC.md](spec/SPEC.md)，包括：

- 容器结构
- content.md 排第一的约定（AI 极速读取核心）
- 魔数标识
- 压缩策略
- 元数据 Schema
- 扩展机制
- 快速读取算法
- 安全考虑

## 目录结构

```
aidoc/
├── bin/
│   └── aidoc              # CLI 可执行入口
├── src/
│   ├── aidoc.py           # 统一 CLI 工具
│   └── setup.py           # pip 安装配置
├── spec/
│   └── SPEC.md            # 格式规范文档
├── examples/
│   ├── example.md          # 示例文件
│   └── example.aidoc       # 示例 AIDOC
├── docs/                   # 文档与资源
├── LICENSE                 # MIT 协议
└── README.md               # 本文件
```

## 设计理念

### 为什么要用 ZIP？

- ZIP 是**通用标准**，所有操作系统和编程语言原生支持
- ZIP 允许**随机访问**单个文件，无需解压整个包
- ZIP 的 `STORED` 模式让关键文件（content.md）保持零开销读取

### content.md 为什么排第一？

这是 AIDOC 格式最重要的约定：content.md 永远是 ZIP 中的第一个条目，STORED 存储，无 data descriptor，无 extra field。

这意味着 AI 读取 MD 内容时，**无需解析 ZIP 中央目录**，直接从 offset 40 读取即可：

```
1. 读取 30B local file header → 找到偏移和大小
2. Seek + Read → 得到 Markdown 内容

整个流程：1 次 seek + 2 次 read，约 10-20μs
```

与通过 ZIP 中央目录读取相比：

| 方式 | seek 次数 | 需要解析 |
|------|:---------:|:--------:|
| 极速模式（本方案） | 1 | ❌ |
| 标准 ZIP 读取 | 2+ | ✅ 需要解析中央目录 |

### 为什么不压缩 .docx/.pdf？

- `.docx`/`.xlsx`/`.pptx` 本身就是 ZIP 包
- `.pdf` 内部已使用 FlateDecode 等压缩流
- `.jpg`/`.png` 已是压缩格式
- 二次压缩得不偿失，使用 `STORED` 模式让这些文件保持原样

## 路线图

- [x] 核心规范 (SPEC.md)
- [x] CLI 工具 (打包/读取/提取)
- [x] 数字签名 (PKCS#7 / 国密 SM2)
- [ ] iCloud / 企业微信集成插件
- [ ] LangChain / LlamaIndex 集成
- [ ] 自动 Word/PDF → Markdown 转换
- [ ] VS Code 扩展（预览/创建）
- [ ] 证标委行业标准预研提案

## 贡献

欢迎通过 Issue 和 PR 参与贡献。

## 许可证

[MIT](LICENSE) © 2026 旗鱼

---

> **AIDOC** — 让 AI 和人类读同一份文件，但用各自最舒服的方式。
