---
name: xlsx
description: "Use this skill any time a spreadsheet file is the primary input or output. This means any task where the user wants to: open, read, edit, or fix an existing .xlsx, .xlsm, .csv, or .tsv file (e.g., adding columns, computing formulas, formatting, charting, cleaning messy data); create a new spreadsheet from scratch or from other data sources; or convert between tabular file formats. Trigger especially when the user references a spreadsheet file by name or path — even casually (like \"the xlsx in my downloads\") — and wants something done to it or produced from it. Also trigger for cleaning or restructuring messy tabular data files (malformed rows, misplaced headers, junk data) into proper spreadsheets. The deliverable must be a spreadsheet file. Do NOT trigger when the primary deliverable is a Word document, HTML report, standalone Python script, database pipeline, or Google Sheets API integration, even if tabular data is involved."
license: Proprietary. LICENSE.txt has complete terms
---

# Requirements for Outputs

## All Excel files

### Professional Font
- Use a consistent, professional font (e.g., Arial, Times New Roman) for all deliverables unless otherwise instructed by the user

### Zero Formula Errors
- Every Excel model MUST be delivered with ZERO formula errors (#REF!, #DIV/0!, #VALUE!, #N/A, #NAME?)

### Preserve Existing Templates (when updating templates)
- Study and EXACTLY match existing format, style, and conventions when modifying files
- Never impose standardized formatting on files with established patterns
- Existing template conventions ALWAYS override these guidelines

## Financial models

### Color Coding Standards
Unless otherwise stated by the user or existing template

#### Industry-Standard Color Conventions
- **Blue text (RGB: 0,0,255)**: Hardcoded inputs, and numbers users will change for scenarios
- **Black text (RGB: 0,0,0)**: ALL formulas and calculations
- **Green text (RGB: 0,128,0)**: Links pulling from other worksheets within same workbook
- **Red text (RGB: 255,0,0)**: External links to other files
- **Yellow background (RGB: 255,255,0)**: Key assumptions needing attention or cells that need to be updated

### Number Formatting Standards

#### Required Format Rules
- **Years**: Format as text strings (e.g., "2024" not "2,024")
- **Currency**: Use $#,##0 format; ALWAYS specify units in headers ("Revenue ($mm)")
- **Zeros**: Use number formatting to make all zeros "-", including percentages (e.g., "$#,##0;($#,##0);-")
- **Percentages**: Default to 0.0% format (one decimal)
- **Multiples**: Format as 0.0x for valuation multiples (EV/EBITDA, P/E)
- **Negative numbers**: Use parentheses (123) not minus -123

### Formula Construction Rules

#### Assumptions Placement
- Place ALL assumptions (growth rates, margins, multiples, etc.) in separate assumption cells
- Use cell references instead of hardcoded values in formulas
- Example: Use =B5*(1+$B$6) instead of =B5*1.05

#### Formula Error Prevention
- Verify all cell references are correct
- Check for off-by-one errors in ranges
- Ensure consistent formulas across all projection periods
- Test with edge cases (zero values, negative numbers)
- Verify no unintended circular references

#### Documentation Requirements for Hardcodes
- Comment or in cells beside (if end of table). Format: "Source: [System/Document], [Date], [Specific Reference], [URL if applicable]"
- Examples:
  - "Source: Company 10-K, FY2024, Page 45, Revenue Note, [SEC EDGAR URL]"
  - "Source: Company 10-Q, Q2 2025, Exhibit 99.1, [SEC EDGAR URL]"
  - "Source: Bloomberg Terminal, 8/15/2025, AAPL US Equity"
  - "Source: FactSet, 8/20/2025, Consensus Estimates Screen"

# XLSX creation, editing, and analysis

## Overview

A user may ask you to create, edit, or analyze the contents of an .xlsx file. You have different tools and workflows available for different tasks.

## Important Requirements

**LibreOffice Required for Formula Recalculation**: You can assume LibreOffice is installed for recalculating formula values using the `scripts/recalc.py` script. The script automatically configures LibreOffice on first run, including in sandboxed environments where Unix sockets are restricted (handled by `scripts/office/soffice.py`)

**CRITICAL — Always copy the original file before any openpyxl modifications.** If `wb.save()` fails mid-write, the file becomes a partial zip missing `[Content_Types].xml` and other critical XML files, rendering it unopenable. See `references/xlsx-corruption-recovery.md` for recovery if corruption occurs.

### Pivot Table Limitation

**openpyxl CANNOT create pivot tables from scratch.** The `pivot.table` module is read-only (preserves existing pivots only). When tasks require "creating a pivot table":

1. **Preferred**: Compute with `pandas.pivot_table()`, write values to target cells with openpyxl formatting
2. **Avoid**: LibreOffice UNO macros for pivot creation — they hang/fail silently in headless mode

See `references/pivot-table-workaround.md` for complete guidance.

## Reading and analyzing data

### Data analysis with pandas
For data analysis, visualization, and basic operations, use **pandas** which provides powerful data manipulation capabilities:

```python
import pandas as pd

# Read Excel
df = pd.read_excel('file.xlsx')  # Default: first sheet
all_sheets = pd.read_excel('file.xlsx', sheet_name=None)  # All sheets as dict

# Analyze
df.head()      # Preview data
df.info()      # Column info
df.describe()  # Statistics

# Write Excel
df.to_excel('output.xlsx', index=False)
```

## Excel File Workflows

## CRITICAL: Use Formulas, Not Hardcoded Values

**Always use Excel formulas instead of calculating values in Python and hardcoding them.** This ensures the spreadsheet remains dynamic and updateable.

### ❌ WRONG - Hardcoding Calculated Values
```python
# Bad: Calculating in Python and hardcoding result
total = df['Sales'].sum()
sheet['B10'] = total  # Hardcodes 5000

# Bad: Computing growth rate in Python
growth = (df.iloc[-1]['Revenue'] - df.iloc[0]['Revenue']) / df.iloc[0]['Revenue']
sheet['C5'] = growth  # Hardcodes 0.15

# Bad: Python calculation for average
avg = sum(values) / len(values)
sheet['D20'] = avg  # Hardcodes 42.5
```

### ✅ CORRECT - Using Excel Formulas
```python
# Good: Let Excel calculate the sum
sheet['B10'] = '=SUM(B2:B9)'

# Good: Growth rate as Excel formula
sheet['C5'] = '=(C4-C2)/C2'

# Good: Average using Excel function
sheet['D20'] = '=AVERAGE(D2:D19)'
```

This applies to ALL calculations - totals, percentages, ratios, differences, etc. The spreadsheet should be able to recalculate when source data changes.

## Common Workflow
1. **Choose tool**: pandas for data, openpyxl for formulas/formatting
2. **Create/Load**: Create new workbook or load existing file
3. **Modify**: Add/edit data, formulas, and formatting
4. **Save**: Write to file
5. **Recalculate formulas (MANDATORY IF USING FORMULAS)**: Use the scripts/recalc.py script
   ```bash
   python scripts/recalc.py output.xlsx
   ```
6. **Verify and fix any errors**: 
   - The script returns JSON with error details
   - If `status` is `errors_found`, check `error_summary` for specific error types and locations
   - Fix the identified errors and recalculate again
   - Common errors to fix:
     - `#REF!`: Invalid cell references
     - `#DIV/0!`: Division by zero
     - `#VALUE!`: Wrong data type in formula
     - `#NAME?`: Unrecognized formula name

### Creating new Excel files

```python
# Using openpyxl for formulas and formatting
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

wb = Workbook()
sheet = wb.active

# Add data
sheet['A1'] = 'Hello'
sheet['B1'] = 'World'
sheet.append(['Row', 'of', 'data'])

# Add formula
sheet['B2'] = '=SUM(A1:A10)'

# Formatting
sheet['A1'].font = Font(bold=True, color='FF0000')
sheet['A1'].fill = PatternFill('solid', start_color='FFFF00')
sheet['A1'].alignment = Alignment(horizontal='center')

# Column width
sheet.column_dimensions['A'].width = 20

wb.save('output.xlsx')
```

### Editing existing Excel files

```python
# Using openpyxl to preserve formulas and formatting
from openpyxl import load_workbook

# Load existing file
wb = load_workbook('existing.xlsx')
sheet = wb.active  # or wb['SheetName'] for specific sheet

# Working with multiple sheets
for sheet_name in wb.sheetnames:
    sheet = wb[sheet_name]
    print(f"Sheet: {sheet_name}")

# Modify cells
sheet['A1'] = 'New Value'
sheet.insert_rows(2)  # Insert row at position 2
sheet.delete_cols(3)  # Delete column 3

# Add new sheet
new_sheet = wb.create_sheet('NewSheet')
new_sheet['A1'] = 'Data'

wb.save('modified.xlsx')
```

## Recalculating formulas

Excel files created or modified by openpyxl contain formulas as strings but not calculated values. Use the provided `scripts/recalc.py` script to recalculate formulas:

```bash
python scripts/recalc.py <excel_file> [timeout_seconds]
```

Example:
```bash
python scripts/recalc.py output.xlsx 30
```

The script:
- Automatically sets up LibreOffice macro on first run
- Recalculates all formulas in all sheets
- Scans ALL cells for Excel errors (#REF!, #DIV/0!, etc.)
- Returns JSON with detailed error locations and counts
- Works on both Linux and macOS

## Formula Verification Checklist

Quick checks to ensure formulas work correctly:

### Essential Verification
- [ ] **Test 2-3 sample references**: Verify they pull correct values before building full model
- [ ] **Column mapping**: Confirm Excel columns match (e.g., column 64 = BL, not BK)
- [ ] **Row offset**: Remember Excel rows are 1-indexed (DataFrame row 5 = Excel row 6)

### Common Pitfalls
- [ ] **NaN handling**: Check for null values with `pd.notna()`
- [ ] **Far-right columns**: FY data often in columns 50+
- [ ] **Multiple matches**: Search all occurrences, not just first
- [ ] **Division by zero**: Check denominators before using `/` in formulas (#DIV/0!)
- [ ] **Wrong references**: Verify all cell references point to intended cells (#REF!)
- [ ] **Cross-sheet references**: Use correct format (Sheet1!A1) for linking sheets
- [ ] **Save failure → file corruption**: If `wb.save()` raises, the file is a partial zip. Always copy the original first. See `references/xlsx-corruption-recovery.md` for recovery.
- [ ] **Pivot table creation**: openpyxl cannot create pivot tables. Use pandas `pivot_table()` + write to cells. See `references/pivot-table-workaround.md`.
- [ ] **TableStyleInfo lost on re-save**: After modifying a file that already has a table, re-verify `table.tableStyleInfo` is set before final save — it can be silently dropped.
- [ ] **`insert_rows` shifts template rows down**: Insert FIRST, then read template style from the new shifted row index (see below).
- [ ] **Cell-level fill does NOT propagate vertically**: When inserting colored rows, each new cell's `fill` must be set explicitly via `template.fill.copy()`. Verify by reading back `cell.fill.start_color.rgb` for inserted rows.

### `insert_rows` + copied styles pitfall (from real merge work)

`ws.insert_rows(idx, amount=N)` pushes existing rows DOWN. If you save a "template" row reference BEFORE the insert and try to copy its style AFTER, the template has already moved. Correct order:

```python
# 1. Insert FIRST (push existing rows down)
ws.insert_rows(idx, amount=N)

# 2. Read template style from the NEW shifted position (idx + N)
for off in range(N):
    new_row = idx + off
    template = ws.cell(row=idx + N, column=col)  # the OLD row idx is now here
    for c in range(1, max_col + 1):
        cell = ws.cell(row=new_row, column=c)
        cell.fill = template.fill.copy()  # explicit copy — no vertical inheritance
        cell.font = template.font.copy()
        cell.border = template.border.copy()
        cell.alignment = template.alignment.copy()

# 3. Now write new data
```

If you write first and copy styles second, newly inserted rows inherit openpyxl defaults (often NO fill) — silently dropping the user's color coding on bulk inserts. **Always verify by reading back `cell.fill.start_color.rgb` for at least 3 inserted rows after the operation.**

### Merged cells + `insert_rows`

`insert_rows` does not always shift merged-cell ranges correctly across openpyxl versions. If the header has `merge_cells(start_row=1, start_column=1, end_row=1, end_column=N)`, inserting near the top may break or duplicate the merge. Workarounds:
1. Unmerge before insert, then re-merge after.
2. Or build new data into a fresh sheet, then move it.

### `execute_code` sandbox state doesn't persist

Each `execute_code` call runs a fresh Python process — `wb`, `ws`, intermediate variables all reset. For sequences of 5+ openpyxl operations with shared state, write a script to `/tmp/` with `write_file` and run via `terminal(command=…)`. Much faster than paging state through repeated execute_code calls.

### Formula Testing Strategy
- [ ] **Start small**: Test formulas on 2-3 cells before applying broadly
- [ ] **Verify dependencies**: Check all cells referenced in formulas exist
- [ ] **Test edge cases**: Include zero, negative, and very large values

### Interpreting scripts/recalc.py Output
The script returns JSON with error details:
```json
{
  "status": "success",           // or "errors_found"
  "total_errors": 0,              // Total error count
  "total_formulas": 42,           // Number of formulas in file
  "error_summary": {              // Only present if errors found
    "#REF!": {
      "count": 2,
      "locations": ["Sheet1!B5", "Sheet1!C10"]
    }
  }
}
```

## Best Practices

### Library Selection
- **pandas**: Best for data analysis, bulk operations, and simple data export
- **openpyxl**: Best for complex formatting, formulas, and Excel-specific features

### Working with openpyxl
- Cell indices are 1-based (row=1, column=1 refers to cell A1)
- Use `data_only=True` to read calculated values: `load_workbook('file.xlsx', data_only=True)`
- **Warning**: If opened with `data_only=True` and saved, formulas are replaced with values and permanently lost
- For large files: Use `read_only=True` for reading or `write_only=True` for writing
- Formulas are preserved but not evaluated - use scripts/recalc.py to update values

### Working with pandas
- Specify data types to avoid inference issues: `pd.read_excel('file.xlsx', dtype={'id': str})`
- For large files, read specific columns: `pd.read_excel('file.xlsx', usecols=['A', 'C', 'E'])`
- Handle dates properly: `pd.read_excel('file.xlsx', parse_dates=['date_column'])`

## 高考志愿填报表 (志愿表) — specific workflow

This pattern recurs for users filling 高考志愿 (gaokao志愿) tables. The spreadsheet usually has columns:

| A 志愿序号 | B 专业组代码 | C 院校名称 | D 专业代码 | E 专业名称 | F-K 分数/学费/学制/招生人数... |

The "real" semantics of志愿填报 — and what the user means by "修正/合并单元格":

- A **志愿位次** = one院校's one专业组. Each志愿 occupies 1..6 majors in the table, all sharing the same A/B/C values.
- The "志愿序号" in column A is an integer 1..N counting志愿位次, NOT a string like "专业组1/2/3...". The original column-A "专业组X" labels are user-side shorthand and must be replaced by integer序号.
- Adjacent rows with identical (B=专业组代码 AND C=院校名称) = same志愿位次 → must be merged into one group.
- Each志愿位次 can have **at most 6 majors** (教育部规则, sometimes "最多4个" in older systems). Flag any group with >6 majors.
- Always unmerge everything first, then re-merge from scratch using the scanned row ranges — don't trust existing merges.

### Algorithm

```python
# 1. Backup the original FIRST (raw open() on /mnt/e/ — see NTFS pitfall below)
with open(SRC, 'rb') as f: data = f.read()
with open(BACKUP, 'wb') as f: f.write(data)

# 2. Unmerge everything
for mr in list(ws.merged_cells.ranges): ws.unmerge_cells(str(mr))

# 3. Scan: group rows where A/B/C any-non-empty starts a new group, empty continues it
groups = []
current = None
for r in range(data_start_row, max_row + 1):
    a, b, c, d = [ws.cell(row=r, column=col).value for col in (1,2,3,4)]
    if a is not None or b is not None or c is not None:
        if current: groups.append(current)
        current = {'row_start': r, 'code': b, 'school': c, 'majors': [(d, r)]}
    else:
        if current: current['majors'].append((d, r))
if current: groups.append(current)

# 4. Coalesce adjacent groups with identical (code, school) — that's the real志愿位次
merged = []
i = 0
while i < len(groups):
    g = groups[i]
    g['row_end'] = g['majors'][-1][1]
    j = i + 1
    while j < len(groups):
        if (groups[j]['code'] == g['code'] and groups[j]['school'] == g['school']
                and groups[j]['row_start'] == g['row_end'] + 1):
            g['majors'].extend(groups[j]['majors'])
            g['row_end'] = groups[j]['majors'][-1][1]
            j += 1
        else: break
    merged.append(g)
    i = j

# 5. Write志愿序号 (integer) to A column top-left, clear other rows, merge A/B/C
for idx, g in enumerate(merged, 1):
    ws.cell(row=g['row_start'], column=1, value=idx)
    for r in range(g['row_start'] + 1, g['row_end'] + 1):
        ws.cell(row=r, column=1).value = None
    if g['row_end'] > g['row_start']:
        ws.merge_cells(start_row=g['row_start'], start_column=1, end_row=g['row_end'], end_column=1)
        ws.merge_cells(start_row=g['row_start'], start_column=2, end_row=g['row_end'], end_column=2)
        ws.merge_cells(start_row=g['row_start'], start_column=3, end_row=g['row_end'], end_column=3)
```

### Pitfalls specific to志愿表 work

- **"专业组X" 字符串 vs 整数志愿序号**: the original A column contains label strings like "专业组1/2/3..." which are NOT the志愿序号 — the志愿序号 is an integer that counts unique志愿位次. Always overwrite with integer.
- **Different院校 can share the same "专业组X" label** (e.g. two different schools both with "专业组7"). Use B+C as the merge key, not the A label.
- **Same院校同一个专业组代码 may appear non-contiguously** if the user re-ordered rows manually. Decide policy: merge only adjacent rows (most conservative, matches user's visible intent) vs merge all (more aggressive, may violate user's explicit ordering).
- **Verify ≤6 majors per group** after scanning; flag violations before saving so the user can decide which to drop.

## Platform-Specific Pitfalls

### Windows-NTFS-mounted `/mnt/e/` (or `/mnt/c/`) backups fail

When the xlsx lives on a Windows drive mounted at `/mnt/e/...` (or similar) inside WSL, `shutil.copy2()` and `shutil.copy()` BOTH fail with `PermissionError: Operation not permitted` because they try to set utime/chmod which NTFS rejects for the WSL-mounted view.

Workaround: read/write the bytes directly.

```python
# ❌ Both fail on /mnt/e/
shutil.copy2(SRC, BACKUP)   # PermissionError on utime
shutil.copy(SRC, BACKUP)    # PermissionError on chmod

# ✅ Works on NTFS mounts
with open(SRC, 'rb') as f: data = f.read()
with open(BACKUP, 'wb') as f: f.write(data)
```

This also means `wb.save(path)` may fail if openpyxl tries to set file metadata — if so, save to `/tmp/` first then copy bytes.

### Python 3.14 + openpyxl: `Fill() takes no arguments`

openpyxl (all versions up to 3.1.5) crashes on **Python 3.14** (Arch, etc.) with:

```
TypeError: Fill() takes no arguments
```

This is a known incompatibility — the `__init_subclass__` change in Python 3.14 breaks openpyxl's style deserialization. Neither `load_workbook()` nor pandas (which uses openpyxl backend) works. Creating a Python 3.12 venv with `uv venv --python 3.12` doesn't help — the same file can trigger the same error in 3.12 if its styles.xml is complex.

**Fallback: Parse the raw XML inside the xlsx zip.** xlsx is a ZIP archive. Unzip it, read `xl/sharedStrings.xml` for string table, then `xl/worksheets/sheet1.xml` for cell data. Use `xml.etree.ElementTree` to walk rows and cells, resolving `t="s"` cells against the shared strings index.

Recipe (see `references/xlsx-xml-fallback.md` for full script):

```python
import zipfile, xml.etree.ElementTree as ET
ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'

with zipfile.ZipFile('file.xlsx') as z:
    # String table
    ss = ET.parse(z.open('xl/sharedStrings.xml'))
    strings = [''.join(t.text or '' for t in si.iter(f'{{{ns}}}t')) for si in ss.getroot()]
    # Sheet data
    sheet = ET.parse(z.open('xl/worksheets/sheet1.xml'))
    for row in sheet.findall(f'.//{{{ns}}}row'):
        for c in row.findall(f'{{{ns}}}c'):
            v = c.find(f'{{{ns}}}v')
            val = strings[int(v.text)] if c.get('t') == 's' and v is not None else (v.text if v is not None else '')
```

## Code Style Guidelines
**IMPORTANT**: When generating Python code for Excel operations:
- Write minimal, concise Python code without unnecessary comments
- Avoid verbose variable names and redundant operations
- Avoid unnecessary print statements

**For Excel files themselves**:
- Add comments to cells with complex formulas or important assumptions
- Document data sources for hardcoded values
- Include notes for key calculations and model sections