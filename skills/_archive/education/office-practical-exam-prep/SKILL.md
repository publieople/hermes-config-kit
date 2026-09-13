---
name: office-practical-exam-prep
description: Prepare for and drill Office practical exams (Word + Excel + Access) — BTEC / HND / ITAS2-style supervised open-book assessments with pre-exam materials gathering, themed tasks (typically 20-30 task booklet), file-format restrictions, and no internet. Use when user asks for exam practice, mentions ITAS2 / HP12 48 / BTEC IT / HND Computing practical, or hands over an Assessment booklet + Required Materials notice.
---

# Office Practical Exam Prep

A repeatable workflow for **supervised, open-book, no-internet** Office practical exams. The deliverable is twofold:
1. A **U-disk of raw materials** (text + images) the candidate brings into the exam
2. A **task-by-task drill** that builds muscle memory on the specific Office operations

## Source disambiguation — do this FIRST

When the user hands over exam materials, expect **multiple documents**:
- An **Assessment / Re-Assessment booklet** (the actual exam questions, may include practice samples)
- A **Required Materials / Pre-Examination Notice** (the rules + what to bring)
- An **Answer Key / Review Solution** (often a previous cohort's solution, looks similar to the real exam)

**Pitfall (high-confidence trap)**: Practice samples and real exam notices often share theme names, table names, or task wording. Conflating them produces wrong U-disk content. Always:

1. **Read every doc end-to-end before generating anything**.
2. **Identify the theme** (company name, product type, branding) of the **real exam** — it's usually stated in the Required Materials notice under "Brand Identity".
3. **Confirm with the user** if two docs disagree on theme, before producing U-disk content.

If theme is "Vibe Digital Experience Centre" in the notice but "Eden Garden Centre" in the booklet, the **notice wins** (it's the real exam); the booklet is practice.

## U-disk contents (per Required Materials notice)

Required format: **`.txt` + `.jpg` / `.png` only**. Never `.docx`, `.xlsx`, `.accdb`, `.dotx` — bringing pre-formatted files = academic misconduct = grade U.

Standard layout on the U-disk:
```
<U-disk root>/
├── vibe_materials.txt         # single consolidated .txt with everything
│   ├── [Personal Info]        # full English name, candidate ID, class section
│   ├── [Tech News URL]        # for hyperlink task (Task 25 typically)
│   ├── [Smart Gadgets ×4]     # name, category (exact spelling), unit cost, 50-80 word description
│   └── [Smart Appliances ×3]  # name, room placement (exact spelling), 50-80 word description
└── images/                    # one .jpg per product, named <category>_<product>.jpg
```

### Critical constraints

- **Category spelling is exact-match** — Wearables / Smart Home / Audio / Living Room / Kitchen / Bedroom. Any space, capitalization, or synonym will be rejected by Access combo box validation. **Never write "Smart-Home" or "smart home" or "SmartHome"**.
- **URL** — use the URL the **teacher / notice explicitly gave**. Do not substitute examples from the notice ("such as TechCrunch..."). The examples are illustrative, not authoritative.
- **Product descriptions** — 50-80 words each, covering features + maintenance/usage notes. Can be self-authored; the notice allows "research and prepare" but the exam is offline so realism > literal research.
- **Images** — solid-color placeholders are fine. Naming convention must let the candidate identify the right image during the timed exam.

### What NOT to include

- No Logo image. The exam typically requires drawing the logo from scratch with Drawing Toolbar shapes (test of Office skills). A pre-made image defeats the purpose.
- No pre-formatted Word/Excel files. Strictly `.txt` + image binaries.

## Task-by-task drill pattern

Practical exam booklets are typically 20-30 tasks. Two valid drill strategies; ask the user which:

1. **Full-walkthrough-first** — explain every task's operations end-to-end, then do. User picks this when unfamiliar with the tool/syllabus.
2. **Drill-each-task** — issue one task, wait for "Task X done", critique against the answer key, then move on. Slower but tighter feedback loop.

For BTEC IT / ITAS2 specifically, the task distribution is roughly:
- Word: 8-10 tasks (logos, cover, table-of-contents, mail merge, footnotes, captions, indexes, document protection, two-column layout)
- Excel: 8-10 tasks (formulas, autofill, AutoSum, conditional formatting, filter, VLOOKUP, PivotTables, charts, macros, shared workbooks)
- Access: 6-8 tasks (table design with input masks / lookups / hyperlinks, database documenter, import spreadsheet wizard, relationships, queries, forms, reports)

### Common high-frequency pitfalls (encountered in real exam keys)

- **Task 3 (Word)** must save as **`.dotx`** (Word Template), not `.dot` or `.docx`. `Save As → Word Template (*.dotx)`.
- **Task 5/6 (Word)** page-header/footer must include candidate name — pattern: `<Name> | Task<N> | <DocName> | <Date>` separated by `|`.
- **Task 10/21 (Excel)** `Ctrl+~` toggles formula/value view. Both views need separate PDF exports.
- **Task 16 (Word Mail Merge)** Label density: default is 30/page (3×10). If the exam asks for 21/page, that's 3×7 — change via Label Options. Master Letter (pre-merge) and Letters (post-merge) are **two separate PDFs**.
- **Task 19 (Excel)** "Compare and Merge Workbooks" is **not on the ribbon by default**. Add via `File → Options → Quick Access Toolbar → All Commands`.
- **Task 23-24 (Access)** Overtime/aggregate fields go in **Report Footer**, never Detail (which would sum per row).

## Workflow rules

- **One .txt, multiple sections** is preferred over many small .txt files — easier to scan during a timed exam.
- **Images named by category + product** so the candidate doesn't fumble with file pickers under time pressure.
- **Always confirm with the user** before generating fictional product names / descriptions / URLs — they may want different content or may have teacher-provided material they haven't shared yet.
- **Acknowledge what is self-authored** when generating creative content (product names, descriptions). The user may not realize content was fabricated, and may need to swap it for real data.

## Pitfall log

- **Conflating practice with real exam** — happened this session. The Chinese Eden-themed booklet was practice; the English Vibe-themed notice was the real exam. Generated Eden-themed U-disk first, wasted work.
- **Fabricating data without disclosure** — generated 7 product names + descriptions without flagging they were self-authored. User had to ask "where did this come from".
- **Substituting URL examples for authoritative URLs** — used `theverge.com` (from the notice's examples list) instead of the teacher-provided `vibedigital.solutions/`. The examples are illustrative; teacher-provided values are authoritative.
- **Long lectures when user wanted overview** — first response went straight to per-task detail. User wanted a complete walkthrough first, then drill. Always ask which mode.

## Related

- Source disambiguation pattern also applies to **assignment / coursework** materials — confirm what's the actual deliverable vs what's a sample before generating.