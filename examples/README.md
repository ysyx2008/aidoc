# AIDOC 示例

## 文件说明

| 文件 | 说明 |
|:----|:------|
| `demo.aidoc` | 打包后的 AIDOC 容器（Word + PDF + 图片 + MD 摘要） |
| `demo.md` | AIDOC 内部的 content.md（AI 摘要） |
| `项目需求说明书.docx` | Word 原始文档 |
| `项目需求说明书-英文版.pdf` | PDF 原始文档 |
| `技术栈架构图.png` | 图片附件 |
| `项目里程碑.png` | 图片附件 |
| `generate_samples.py` | 生成上述示例文件的脚本 |

## 使用方式

```bash
# 查看 AIDOC 内容
aidoc view examples/demo.aidoc

# 极速读取 AI 摘要
aidoc md examples/demo.aidoc

# 查看元数据和文件清单
aidoc info examples/demo.aidoc

# 提取所有原始文件
aidoc extract examples/demo.aidoc ./导出

# 签名 + 验签
aidoc sign examples/demo.aidoc --gen-key
aidoc verify examples/demo.aidoc
```

## 重新生成

```bash
cd examples
python3 generate_samples.py
aidoc create 项目需求说明书.docx 项目需求说明书-英文版.pdf 技术栈架构图.png 项目里程碑.png demo.md -o demo.aidoc
```

---

> 示例版本：v0.1.0
