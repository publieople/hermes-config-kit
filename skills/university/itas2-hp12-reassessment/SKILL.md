---
name: itas2-hp12-reassessment
description: ITAS2 (HP12 48) 补考实战工作流 — Concord University College / 福建师大协和学院的 Office 实践考试，含考前素材准备、27 Task 操作清单、Access/Word/Excel 关键坑
---

# ITAS2 (HP12 48) 实践考试 补考

> 课程:Information Technology: Applications Software 2
> 学校:Concord University College, Fujian Normal University (福建师大协和学院)

## 考试形式(硬约束)

- **开卷但禁网**:监考电脑完全断网,office 文件直接拷入答卷
- **只允许 U 盘带 .txt + .jpg/.png**;预制 .docx/.xlsx → 学术不端 → U 级
- **监考查 U 盘**,带违规文件当场判定
- **3 小时 27 个 Task**,Word + Excel + Access 综合

## ⚠️ 必避陷阱: 区分"练习题" vs "明天真考"

很多老师发**两份 PDF**:
- 一份是 **练习题 / 答案册**(中英都可能,带 Eden / CUC / Vibe 旧主题)
- 一份是 **正式考前通知**(Required Materials & Data Collection,带新主题如 Vibe)

**操作前必须问用户哪份是真考**,而不是自行从两个主题里挑一个下手。
判断方法:
- 看 PDF 标题:`Required Materials` / `考前通知` / `pre-exam notice` = 真考
- 看 PDF 是否列出"4 种 smart gadgets"等新主题描述 = 真考
- 中文版 PDF + Eden 主题 = 多半是练习

## 考前素材准备(放 U 盘)

### 1 个总 .txt(必备)

```txt
[Personal Info]
Full English Name: <英文名>
Candidate ID Number: <学号>
Class Section: <班级>

[Tech News URL - Task 25]
https://<老师给的URL>(一般是学校官网)

[Smart Gadgets × 4 - Task 5]
类别必须一字不差: Wearables / Smart Home / Audio

=== 1. <Product Name> ===
Category: <准确类别>
Unit Cost: <数字>
Description (50-80 words): <50-80词描述,含规格+维护>
Image: <本地文件名>

[Smart Appliances × 3 - Tasks 11 & 12]
类别必须一字不差: Living Room / Kitchen / Bedroom

=== 5. <Appliance Name> ===
Room Placement: <准确房间>
Description (50-80 words): ...
Image: <本地文件名>
```

**字数核查**:每个 description 必须 50-80 词,考场插入数据库会卡长度。

### 7 张真图(必备)

不要纯色占位!考试要求 "clear digital photograph or vector illustration"。

**首选来源**:Wikimedia Commons(自由许可 + 无 key + 真产品图)
- API:`https://commons.wikimedia.org/w/api.php?action=query&list=search&srnamespace=6&srsearch=<关键词>&srlimit=15&format=json`
- File 命名空间 `6`,搜出 `File:XXX.jpg`
- 拿 imageinfo:`&prop=imageinfo&iiprop=url&iiurlwidth=800`

**已知坑**(用 `media/wikimedia-image-fetch` skill):
1. summary API 返回的缩略图经常是错的(Apple Watch Ultra 2 拿到 Series 3)
2. 默认搜结果包含 PDF → 必须过滤 `.pdf/.svg/.webm/.ogv`
3. upload.wikimedia.org 限流 429 → sleep 60s 再试
4. 必须用真实 User-Agent,默认 `python-requests` 会被拦

## 27 Task 操作清单

按考试通知 / 答案册,完整 Task 列表见 `references/27-task-playbook.md`。

**关键高频 Task 套路**:

| Task | 套路 |
|------|------|
| Task 3 | Save As → Word Template `.dotx`,**不是 .docx,不是 .dot** |
| Task 4 Access | Database Tools → Database Documenter → Options → PDF |
| Task 5/6 Word | Heading 2 样式默认隐藏 → Style Pane Options → Show All Styles |
| Task 5 Word | 1 页 3 种花 + Keep with next 避免跨页 |
| Task 5 Word | 页脚格式:`<姓名> \| Task5 \| Flowers \| <日期>`(Tab 分隔) |
| Task 6 Word | Restrict Editing → Comments(题目说"无法添加批注") |
| Task 7/9 Macro | Alt+F11 看 VBA 代码,截图 Sub...End Sub |
| Task 10 Excel | Ctrl+~ 切值/公式视图 → **两个视图各导一份 PDF** |
| Task 14 Excel | 筛选 Sun=Yes AND DOB > #1975-01-01# → 复制到 A70 |
| Task 16 Mail Merge | Labels 默认 30/页,题目要 **21/页(3×7)** → 改 Label Options |
| Task 16 Mail Merge | Master Letter(未合并) + Letters(合并后第一页)= **两份 PDF** |
| Task 17 Word | Logo 右键 → Wrap Text → **In Front of Text**(不是 Square) |
| Task 19 Excel | Compare and Merge Workbooks **在 ribbon 隐藏** → 加到 Quick Access Toolbar |
| Task 20 Excel | Lock Cell 默认勾选 → 取消 PM 单元格 Lock → Protect Sheet |
| Task 21 Excel | VLOOKUP 第 4 参数 = FALSE(精确匹配) |
| Task 22 Access | Create → Form → **Multiple Items**(显示多条) |
| Task 23 Access | Relationships 拖字段建关联,Query 自动 join |
| Task 24 Access | Sum 控件放 **Report Footer**(不是 Detail) |

## 输出目录约定

```
E:\ToDo\<CourseName>\
├── <materials>.txt          # 单文件总材料
└── images/                  # 所有真图
```

**示例**:本次任务 → `E:\ToDo\ITAS2_Reassess1\`。

## 考场上 U 盘内容验证清单

考前最后一刻核对:
- [ ] 1 个 .txt 含个人信息 + 4 gadgets + 3 appliances + URL
- [ ] 类别拼写: Wearables / Smart Home / Audio / Living Room / Kitchen / Bedroom
- [ ] 每个 description 词数 ∈ [50, 80]
- [ ] 每个 Image 引用都对应 images/ 下的实际文件
- [ ] 7 张图都是真图(>5KB,非纯色块)
- [ ] URL 用老师给的版本(不要用 The Verge 等举例)
- [ ] **无 .docx/.xlsx/.pptx** 等预制文件