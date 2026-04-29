# AIDOC 示例：使用说明

## 从 Markdown 创建 AIDOC

```bash
# 只有一个 MD 文件时
aidoc create example.md -o example.aidoc --author '于申'

# 查看内容
aidoc md example.aidoc

# 查看元数据
aidoc meta example.aidoc
```

## 从 Word + Markdown + 图片创建

```bash
aidoc create report.docx summary.md cover.png -o report.aidoc
```

## 从模板创建空白文档

```bash
aidoc init -o mydoc.aidoc --title '我的文档'
```

---

本目录下的 `example.aidoc` 是使用以下命令创建的：

```bash
aidoc create example.md -o example.aidoc --author '于申' --tags '示例,演示'
```
