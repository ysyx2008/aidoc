#!/usr/bin/env python3
"""
生成 AIDOC 示例文件

每个示例展示一种文件类型，打包为独立的 .aidoc。
content.md 与原始文档内容严格一致（同一份内容的不同格式）。
"""
import os, sys, subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

AUTHOR = '旗鱼'

# ═══ 统一的文档内容 ═══
# content.md 和原始文档使用同一份内容，只是格式不同

DOC_TITLE = '投行底稿数字平台 — 项目需求说明书'
DOC_DATE = '2026-04-25'
DOC_AUTHOR = '金融科技部'

# 中文版内容
zh_content = f"""# {DOC_TITLE}

版本：v1.0 | 日期：{DOC_DATE} | 编制：{DOC_AUTHOR}

## 一、项目背景

当前投行底稿管理存在以下痛点：

- 底稿文件分散存储，检索困难
- 监管检查时调阅效率低
- 版本管理混乱，无法追溯修改记录
- 缺乏统一文件命名规范

## 二、功能需求

### 2.1 底稿录入

支持 Word、PDF、扫描件等多种格式上传，自动提取文件名、日期等元数据，支持批量导入。

### 2.2 智能检索

基于全文检索的底稿搜索，支持按项目、类型、日期等多维度筛选，支持 OCR 识别扫描件文字。

### 2.3 版本管理

每次修改自动生成新版本，支持版本对比和回溯，操作记录完整可追溯。

### 2.4 监管调阅

一键打包导出底稿包，生成调阅清单，支持水印保护。

## 三、技术方案

| 模块 | 技术选型 | 说明 |
|------|----------|------|
| 前端 | Vue 3 + Element Plus | 管理后台 |
| 后端 | Spring Boot 3 | 微服务架构 |
| 存储 | MinIO + PostgreSQL | 文件及元数据 |
| 搜索 | Elasticsearch | 全文检索 |
| OCR | PaddleOCR | 扫描件文字识别 |

## 四、项目计划

- **2026.05** — 需求评审
- **2026.06** — 系统设计
- **2026.07-08** — 开发阶段
- **2026.09** — 测试阶段
- **2026.10** — 正式上线

---

审批人：张总
"""

# 英文版内容
en_content = f"""# Investment Banking Document Platform — Requirements Specification

Version: v1.0 | Date: {DOC_DATE} | Author: FinTech Dept.

## 1. Background

Current pain points in investment banking document management:

- Documents stored in multiple locations, difficult to retrieve
- Low efficiency when responding to regulatory inspections
- No version control, unable to track changes
- No unified file naming conventions

## 2. Functional Requirements

### 2.1 Document Input

Support upload of Word, PDF, scanned files and other formats. Auto-extract metadata such as file name and date. Support batch import.

### 2.2 Intelligent Search

Full-text search across all documents. Support multi-dimensional filtering by project, type, date. OCR for scanned document text recognition.

### 2.3 Version Management

Auto-generate new version on each modification. Support version comparison and rollback. Complete audit trail.

### 2.4 Regulatory Access

One-click document package export. Generate inspection checklist. Support watermark protection.

## 3. Tech Stack

| Module | Selection | Description |
|--------|-----------|-------------|
| Frontend | Vue 3 + Element Plus | Admin UI |
| Backend | Spring Boot 3 | Microservices |
| Storage | MinIO + PostgreSQL | Files & Metadata |
| Search | Elasticsearch | Full-text search |
| OCR | PaddleOCR | Text recognition |

## 4. Timeline

- **May 2026** — Requirements Review
- **Jun 2026** — System Design
- **Jul-Aug 2026** — Development
- **Sep 2026** — Testing
- **Oct 2026** — Launch

---

Approver: General Manager Zhang
"""

# ═══ 1. Word 示例 ═══
print("📄 Word 示例...")
from docx import Document
from docx.shared import Pt

doc = Document()
style = doc.styles['Normal']
font = style.font
font.name = '宋体'
font.size = Pt(11)

doc.add_heading(DOC_TITLE, 0)
doc.add_paragraph(f'版本：v1.0 | 日期：{DOC_DATE} | 编制：{DOC_AUTHOR}')

doc.add_heading('一、项目背景', 1)
doc.add_paragraph('当前投行底稿管理存在以下痛点：')
for item in ['底稿文件分散存储，检索困难', '监管检查时调阅效率低', '版本管理混乱，无法追溯修改记录', '缺乏统一文件命名规范']:
    doc.add_paragraph(item, style='List Bullet')

doc.add_heading('二、功能需求', 1)
doc.add_heading('2.1 底稿录入', 2)
doc.add_paragraph('支持 Word、PDF、扫描件等多种格式上传，自动提取文件名、日期等元数据，支持批量导入。')
doc.add_heading('2.2 智能检索', 2)
doc.add_paragraph('基于全文检索的底稿搜索，支持按项目、类型、日期等多维度筛选，支持 OCR 识别扫描件文字。')
doc.add_heading('2.3 版本管理', 2)
doc.add_paragraph('每次修改自动生成新版本，支持版本对比和回溯，操作记录完整可追溯。')
doc.add_heading('2.4 监管调阅', 2)
doc.add_paragraph('一键打包导出底稿包，生成调阅清单，支持水印保护。')

doc.add_heading('三、技术方案', 1)
table = doc.add_table(rows=6, cols=3)
table.style = 'Light Shading'
for i, row in enumerate([
    ('模块', '技术选型', '说明'),
    ('前端', 'Vue 3 + Element Plus', '管理后台'),
    ('后端', 'Spring Boot 3', '微服务架构'),
    ('存储', 'MinIO + PostgreSQL', '文件及元数据'),
    ('搜索', 'Elasticsearch', '全文检索'),
    ('OCR', 'PaddleOCR', '扫描件文字识别'),
]):
    for j, cell in enumerate(row):
        table.cell(i, j).text = cell

doc.add_heading('四、项目计划', 1)
for time, task in [('2026.05', '需求评审'), ('2026.06', '系统设计'), ('2026.07-08', '开发阶段'), ('2026.09', '测试阶段'), ('2026.10', '正式上线')]:
    doc.add_paragraph(f'{time}  {task}')

doc.add_paragraph('审批人：张总')
doc.save('_tmp.docx')

# content.md = 与 Word 完全一致的中文 Markdown
with open('_tmp.md', 'w') as f:
    f.write(zh_content)

subprocess.run([sys.executable, '../src/aidoc.py', 'create',
    '_tmp.docx', '_tmp.md',
    '-o', 'demo-word.aidoc',
    '--author', AUTHOR, '--tags', '示例,Word'],
    capture_output=True)
os.remove('_tmp.docx')
os.remove('_tmp.md')
size = os.path.getsize('demo-word.aidoc')
print(f'  ✅ demo-word.aidoc ({size:,} B)')

# ═══ 2. PDF 示例 ═══
print("\n📄 PDF 示例...")
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font('Helvetica', 'B', 16)
pdf.cell(0, 10, 'Investment Banking Document Platform', new_x="LMARGIN", new_y="NEXT", align='C')
pdf.set_font('Helvetica', '', 10)
pdf.cell(0, 8, 'Requirements Specification v1.0', new_x="LMARGIN", new_y="NEXT", align='C')
pdf.cell(0, 8, f'Date: {DOC_DATE} | Author: FinTech Dept.', new_x="LMARGIN", new_y="NEXT", align='C')
pdf.ln(6)

pdf.set_font('Helvetica', 'B', 13)
pdf.cell(0, 10, '1. Background', new_x="LMARGIN", new_y="NEXT")
pdf.set_font('Helvetica', '', 10)
pdf.multi_cell(0, 6, '- Documents stored in multiple locations, difficult to retrieve\n- Low efficiency when responding to regulatory inspections\n- No version control, unable to track changes\n- No unified file naming conventions')
pdf.ln(3)

pdf.set_font('Helvetica', 'B', 13)
pdf.cell(0, 10, '2. Tech Stack', new_x="LMARGIN", new_y="NEXT")
pdf.set_font('Helvetica', '', 10)
pdf.multi_cell(0, 6, 'Frontend: Vue 3 + Element Plus\nBackend: Spring Boot 3\nStorage: MinIO + PostgreSQL\nSearch: Elasticsearch\nOCR: PaddleOCR')
pdf.ln(3)

pdf.set_font('Helvetica', 'B', 13)
pdf.cell(0, 10, '3. Timeline', new_x="LMARGIN", new_y="NEXT")
pdf.set_font('Helvetica', '', 10)
pdf.multi_cell(0, 6, 'May 2026 - Requirements Review\nJun 2026 - System Design\nJul-Aug 2026 - Development\nSep 2026 - Testing\nOct 2026 - Launch')

pdf.output('_tmp.pdf')

# content.md = 与 PDF 完全一致的英文 Markdown
with open('_tmp.md', 'w') as f:
    f.write(en_content)

subprocess.run([sys.executable, '../src/aidoc.py', 'create',
    '_tmp.pdf', '_tmp.md',
    '-o', 'demo-pdf.aidoc',
    '--author', AUTHOR, '--tags', '示例,PDF'],
    capture_output=True)
os.remove('_tmp.pdf')
os.remove('_tmp.md')
size = os.path.getsize('demo-pdf.aidoc')
print(f'  ✅ demo-pdf.aidoc ({size:,} B)')

# ═══ 3. 图片示例 ═══
print("\n🖼️ 图片示例...")
from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGB', (800, 500), 'white')
draw = ImageDraw.Draw(img)
font_t = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 18)
font_s = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 11)

def draw_chart(draw, x, y, w, h, title, labels, values, color):
    draw.text((x + w//2, y + 10), title, fill='#1d1d1f', font=font_t, anchor='mt')
    bar_w, max_h, gap = 40, 120, 20
    sx = x + (w - len(labels) * (bar_w + gap)) // 2
    bl = y + h - 40
    mv = max(values) or 1
    for i, (l, v) in enumerate(zip(labels, values)):
        bh = int(v / mv * max_h)
        bx = sx + i * (bar_w + gap)
        draw.rectangle([bx, bl - bh, bx + bar_w, bl], fill=color)
        draw.text((bx + bar_w//2, bl + 5), str(v), fill='#1d1d1f', font=font_s, anchor='mt')
        lines = l.split('\n')
        for li, line in enumerate(lines):
            draw.text((bx + bar_w//2, bl + 22 + li * 15), line, fill='#86868b', font=font_s, anchor='mt')

draw_chart(draw, 20, 20, 360, 220, '技术栈成熟度',
    ['Vue3', 'Spring\nBoot3', 'MinIO', 'PostgreSQL', 'Elastic\nsearch', 'Paddle\nOCR'],
    [85, 90, 70, 75, 80, 65], '#007aff')

draw_chart(draw, 420, 20, 360, 220, '项目进度',
    ['需求评审', '系统设计', '开发', '测试', '上线'],
    [30, 50, 85, 75, 100], '#34c759')

draw.text((400, 270), f'{DOC_TITLE} — 技术架构与项目计划',
          fill='#1d1d1f', font=font_t, anchor='mt')
draw.rectangle([200, 295, 600, 297], fill='#e8e8ed')
draw.text((400, 315), '左图：技术选型成熟度评估 | 右图：项目里程碑规划',
          fill='#86868b', font=font_s, anchor='mt')

img.save('技术栈架构图.png')

# content.md = 图片内容的文字描述
image_content = f"""# {DOC_TITLE} — 可视化概览

## 技术栈成熟度图（左侧柱状图）

展示各技术模块的成熟度评估：

- Vue 3：85%
- Spring Boot 3：90%
- MinIO：70%
- PostgreSQL：75%
- Elasticsearch：80%
- PaddleOCR：65%

## 项目里程碑图（右侧柱状图）

展示项目进度规划：

- 需求评审：30%
- 系统设计：50%
- 开发：85%
- 测试：75%
- 上线：100%
"""

with open('_tmp.md', 'w') as f:
    f.write(image_content)

subprocess.run([sys.executable, '../src/aidoc.py', 'create',
    '技术栈架构图.png', '_tmp.md',
    '-o', 'demo-image.aidoc',
    '--author', AUTHOR, '--tags', '示例,图片'],
    capture_output=True)
os.remove('技术栈架构图.png')
os.remove('_tmp.md')
size = os.path.getsize('demo-image.aidoc')
print(f'  ✅ demo-image.aidoc ({size:,} B)')

print(f"\n🎉 全部生成完成！共 3 个 AIDOC 示例")