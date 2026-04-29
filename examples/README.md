# AIDOC 示例

## 示例文件

| 文件 | 类型 | 说明 |
|:----|:----|:------|
| `demo-word.aidoc` | Word | content.md + document.docx，中文内容 |
| `demo-pdf.aidoc` | PDF | content.md + document.pdf，英文内容 |
| `demo-image.aidoc` | 图片 | content.md + 技术栈架构图.png |
| `generate_samples.py` | 脚本 | 一键重新生成所有示例 |

## 使用方式

```bash
# 查看 AIDOC 内容（浏览器阅读器）
aidoc view examples/demo-word.aidoc

# 极速读取 Markdown
aidoc md examples/demo-word.aidoc

# 查看文件清单
aidoc ls examples/demo-word.aidoc

# 提取原始文件
aidoc extract examples/demo-word.aidoc ./导出

# 签名验证
aidoc sign examples/demo-word.aidoc --gen-key
aidoc verify examples/demo-word.aidoc
```

## 重新生成

```bash
cd examples
python3 generate_samples.py
```

---

> 示例版本：v0.1.0
