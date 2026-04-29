# Contributing to AIDOC

感谢你对 AIDOC 的关注！🎉

AIDOC 是一个开放的 AI 原生文档格式，欢迎任何形式的贡献——无论是报告 bug、提出功能建议、完善文档，还是提交代码。

## 贡献方式

### 🐛 报告 Bug

如果你发现了 bug，请创建一个 Issue 并包含以下信息：

- 你的操作系统和 Python 版本
- 完整的命令和输出
- 期望行为和实际行为
- 如果可以，提供一个最小复现步骤

### 💡 功能建议

通过 Issue 提交功能建议，描述：

- 你想解决的问题是什么
- 你期望的方案是什么
- 是否有替代方案

### 📖 完善文档

文档和代码同样重要。如果你发现文档有误、不清晰、或缺少示例，欢迎提交 PR。

### 🔧 提交代码

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feat/amazing-feature`)
3. 提交你的改动 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feat/amazing-feature`)
5. 创建一个 Pull Request

## 开发指南

### 环境准备

```bash
# 克隆仓库
git clone https://github.com/your-username/aidoc.git
cd aidoc

# 核心功能无需额外依赖（纯标准库）
# 如需签名功能，安装 cryptography
pip install cryptography
```

### 代码规范

- **Python**: 遵循 PEP 8，使用 4 空格缩进
- **提交信息**: 遵循 [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat:` 新功能
  - `fix:` Bug 修复
  - `docs:` 文档变更
  - `refactor:` 代码重构
  - `test:` 测试相关
  - `chore:` 构建、CI 等杂项

### 运行测试

```bash
# 运行功能审查
bash test-all.sh

# 运行性能基准测试
python3 docs/bench.py
```

### 代码结构

```
aidoc/
├── bin/aidoc            # CLI 入口
├── src/
│   └── aidoc.py         # 主程序（打包、读取、签名）
├── spec/SPEC.md         # 格式规范
├── docs/                # 文档和测试脚本
└── examples/            # 示例
```

### 发布流程

1. 更新 CHANGELOG.md
2. 更新版本号（src/aidoc.py 中的 AIDOC_VERSION）
3. 创建 Git Tag (`git tag v0.1.0`)
4. 推送到 GitHub (`git push --tags`)
5. 在 GitHub Releases 中创建 Release

## 行为准则

请保持友好和尊重。我们的目标是建立一个包容、开放的社区。

## 问题？

有任何问题，欢迎在 Discussions 中提出，或直接联系维护者。

---

再次感谢你的贡献！🌟
