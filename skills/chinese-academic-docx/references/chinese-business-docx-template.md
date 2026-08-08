# Chinese Business Document (方案/报告/规划) — docx-js Template

Proven pattern for generating formal Chinese business documents with docx-js (npm `docx` package). Complements the academic template in SKILL.md — use this for consulting proposals, business plans, and formal reports.

## Structure

```
封面 → 目录 → 正文章节（一、二、三...）→ 附录
```

## Key Patterns

### Document Setup
```js
const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: "Microsoft YaHei", size: 22 },  // 全局默认字体
      },
    },
  },
  numbering: {
    config: [{
      reference: "default-numbering",
      levels: [{
        level: 0,
        format: NumberFormat.DECIMAL,
        text: "%1.",
        alignment: AlignmentType.START,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } },
      }],
    }],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },  // A4
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          children: [
            new TextRun({ text: "文档标题", size: 16, color: "999999" }),
            new TextRun({ text: "\t机密", size: 16, color: "999999" }),
          ],
          tabStops: [{ type: "right", position: 9026 }],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          children: [
            new TextRun({ text: "第 ", size: 16, color: "999999" }),
            new TextRun({ children: [docx.PageNumber.CURRENT], size: 16, color: "999999" }),
            new TextRun({ text: " 页", size: 16, color: "999999" }),
          ],
          alignment: AlignmentType.CENTER,
        })],
      }),
    },
    children: [ /* content */ ],
  }],
});
```

### Cover Page
```js
new Paragraph({ spacing: { before: 3000 } }),  // push content down
new Paragraph({
  children: [new TextRun({ text: "集团名称", size: 56, bold: true, color: "1A1A2E" })],
  alignment: AlignmentType.CENTER,
  spacing: { after: 200 },
}),
new Paragraph({
  children: [new TextRun({ text: "方案标题", size: 48, bold: true, color: "0F3460" })],
  alignment: AlignmentType.CENTER,
  spacing: { after: 400 },
}),
new Paragraph({
  children: [new TextRun({ text: "副标题/技术框架", size: 28, color: "533483" })],
  alignment: AlignmentType.CENTER,
  spacing: { after: 800 },
}),
new Paragraph({
  children: [new TextRun({ text: "Version 0.1  |  2026年8月", size: 22, color: "666666" })],
  alignment: AlignmentType.CENTER,
}),
new Paragraph({ children: [new PageBreak()] }),
```

### Section Headings
```js
// 一级标题：一、二、三...
function heading(text, level = HeadingLevel.HEADING_1) {
  return new Paragraph({
    text,
    heading: level,
    spacing: { before: 400, after: 200 },
    thematicBreak: true,  // adds horizontal rule below
  });
}

// Usage: heading("一、项目背景与目标") → renders as "一、项目背景与目标"
// Usage: heading("1.1 项目背景", HeadingLevel.HEADING_2)
```

### Styled Tables
```js
const TABLE_HEADER_BG = "1A1A2E";
const TABLE_ALT_BG = "F8F9FA";

function headerCell(text, width) {
  return new TableCell({
    children: [new Paragraph({
      children: [new TextRun({ text, size: 20, bold: true, color: "FFFFFF" })],
    })],
    width: { size: width, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: TABLE_HEADER_BG },
    verticalAlign: "center",
  });
}

function tableCell(text, width, options = {}) {
  return new TableCell({
    children: [new Paragraph({
      children: [new TextRun({ text, size: 20, ...options.textOptions })],
    })],
    width: { size: width, type: WidthType.DXA },
    shading: options.shading ? { type: ShadingType.CLEAR, fill: options.shading } : undefined,
    verticalAlign: "center",
  });
}

// Table with alternating row colors
new Table({
  columnWidths: [2500, 3500, 3026],  // must sum to table width
  rows: [
    new TableRow({ children: [headerCell("列1", 2500), headerCell("列2", 3500), headerCell("列3", 3026)] }),
    new TableRow({ children: [
      tableCell("内容", 2500),
      tableCell("内容", 3500),
      tableCell("内容", 3026),
    ]}),
    new TableRow({ children: [  // alternating row
      tableCell("内容", 2500, { shading: TABLE_ALT_BG }),
      tableCell("内容", 3500, { shading: TABLE_ALT_BG }),
      tableCell("内容", 3026, { shading: TABLE_ALT_BG }),
    ]}),
  ],
})
```

### Bullet & Numbered Lists
```js
function bullet(text, level = 0) {
  return new Paragraph({
    children: [new TextRun({ text })],
    bullet: { level },
    spacing: { after: 80, line: 360 },
  });
}

function numbered(text, level = 0) {
  return new Paragraph({
    children: [new TextRun({ text })],
    numbering: { reference: "default-numbering", level },
    spacing: { after: 80, line: 360 },
  });
}
```

### Page Break Between Sections
```js
new Paragraph({ children: [new PageBreak()] }),
```

## Color Palette (Business Dark)

| Role | Hex | Usage |
|------|-----|-------|
| Dark | `1A1A2E` | Main title, table header bg |
| Accent | `16213E` | Subtitle |
| Highlight | `0F3460` | Section title |
| Accent2 | `533483` | Sub-subtitle |
| Light BG | `F0F4F8` | Light background |
| Alt Row | `F8F9FA` | Table alternating rows |
| Gray | `999999` | Header/footer text |

## Verification

```bash
soffice --headless --convert-to pdf output.docx --outdir /tmp/preview
pdftoppm -jpeg -r 100 /tmp/preview/output.pdf /tmp/preview/page
# Inspect with vision_analyze
```

## Pitfalls

- `ShadingType.SOLID` renders black — always use `ShadingType.CLEAR`
- Table `columnWidths` must sum to total table width
- `thematicBreak: true` on heading adds horizontal rule — good for section separation
- Chinese font: `Microsoft YaHei` works well for business docs; `宋体` for academic
- Font size 22 = 11pt, size 20 = 10pt (docx-js uses half-points)
