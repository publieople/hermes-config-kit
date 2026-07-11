# Source Files Inventory — ITAS2 Re-Assessment 1 (2026-07-10)

Verified by extracting `IT2 Reassess.rar` and reading each file's table structure.
Examiner: Concord University College, Fujian Normal University.

## Archives Delivered

```
IT2 Reassess.rar  (48 KB, RAR5)
└── Supplementary Files of IT2 Re-Assessment1/
    ├── vibe_gadgets.accdb     (396 KB) — Smart Gadgets inventory DB
    ├── vibe_employees.accdb   (384 KB) — Staff + Overtime DB
    ├── vibe_operations.xlsx   (18 KB)  — Multi-sheet Excel data
    └── digital_products.docx  (0 bytes — EMPTY, do not rely on)
└── Assessment 1_Answer Template_Re-Assess Cover.doc — answer paper cover template
```

## vibe_gadgets.accdb — Smart_Gadgets Table

| Field | Type | Sample |
|---|---|---|
| Product_Code | ShortText (Primary Key) | V101, V102, … V111 |
| Product_Name | **Hyperlink** (display text + # + URL) | "Vibe Watch Pro#http://www.vibe.com#" |
| Category | ShortText | Wearables / Audio / Smart Home |
| Unit_Cost | Currency (display only — see caveat below) | 12000, 25000, … |
| User_Manual_Text | LongText | generic text block |

**11 records total**. Product codes V101-V111. Three category values exactly: **Wearables**, **Audio**, **Smart Home** (case-sensitive, exact spelling).

⚠ **access-parser quirk**: Unit_Cost shows ×1000 inflated values (12000000 instead of 12000). This is a parser bug — actual field in Access is Currency. Trust what's displayed in Access itself, not the parser dump.

⚠ **Product_Name is already Hyperlink type** — Task 4 likely asks you to verify/conform this, NOT to change it to Hyperlink from something else.

## vibe_employees.accdb

| Table | Fields |
|---|---|
| Staff | Employee_Number (PK), First_Name, Last_Name, Hourly_Rate |
| Overtime_Log | Employee_Number, Date_Worked, Overtime_Hours |

⚠ **access-parser only returned 1 row from each** — actual table likely has more (parser limitation on these specific tables). Trust Access display.

Relationship: `Staff.Employee_Number` ↔ `Overtime_Log.Employee_Number` (one-to-many).

## vibe_operations.xlsx — 5 Sheets

### Sheet 1: Discount_Matrix (9 × 7)
```
R3: Cost per item=15, [Sales/Discount table on right]
    Sales ≥ 25 → 0%; ≥ 50 → 3%; ≥ 75 → 5%; ≥ 100 → 7%; ≥ 150 → 10%; ≥ 200 → 15%
R4-5: Example: 5 items × $15 = $75 → 5% discount
```
**Use for**: Task 17 Order Form discount calculation, possibly Task 8.

### Sheet 2: May_Weekly_Sales (7 × 2)
| Week | Sales (RMB) |
|---|---|
| Thursday Week 1 | 125000 |
| Thursday Week 2 | 142000 |
| Thursday Week 3 | 115000 |
| Thursday Week 4 | 168000 |

**Use for**: Task 8 (Excel autofill + outline grouping on May dates).

### Sheet 3: Client_Subscriptions (20 × 8)
| Client ID | First Name | Surname | Status | Dob | City | Smart Gadgets | Smart Home |
|---|---|---|---|---|---|---|---|
| 1 | Gary | Williams | Mr | 1986-04-12 | Fuzhou | Yes | Yes |
| 2 | Linda | Chen | Mrs | 1988-06-25 | Fuzhou | Yes | Yes |
| 3 | Nicola | Paton | Mr | 1984-11-02 | Xiamen | Yes | Yes |
| 4 | Stephen | Miller | Mr | 1992-03-14 | Fuzhou | Yes | Yes |
| 5 | Audrey | Black | Ms | 1986-07-19 | Fuzhou | No | Yes |
| 6 | Kenneth | Drysdale | Mr | 1980-01-30 | Quanzhou | Yes | Yes |
| 7 | Amanda | Fyfe | Ms | 1995-10-05 | Fuzhou | No | Yes |
| 8 | Kirsty | Brown | Ms | 1987-12-22 | Fuzhou | Yes | Yes |
| 9 | Morgan | Graham | Ms | 1975-05-16 | Xiamen | Yes | No |
| 10 | Laura | Farmer | Mrs | 1989-08-08 | Fuzhou | No | Yes |
| 11 | Rosemary | Lin | Mrs | 1991-02-11 | Fuzhou | Yes | Yes |
| 12 | Donald | Leitch | Mr | 1983-09-21 | Quanzhou | Yes | No |
| 13 | Angus | Sneddon | Ms | 1985-04-03 | Fuzhou | Yes | Yes |
| 14 | Johathan | Sutherland | Mr | 1994-06-18 | Fuzhou | Yes | Yes |
| 15 | Alex | Zhang | Ms | 1990-11-27 | Fuzhou | Yes | Yes |

**Use for**: Task 14 (filter Sun=Yes AND DOB>1975), Task 15 (import to Access → query), Task 16 (mail merge recipients), Task 18 (PivotTable).

Cities: **Fuzhou / Xiamen / Quanzhou** (not the Lauderburgh from the old skill).

### Sheet 4: Inventory_Control (6 × 8)
| Product ID | Product Name | Category | Min Stock Level | Quantity on Hand | Unit Cost | Stock Value | Reorder Status |
|---|---|---|---|---|---|---|---|
| V101 | Vibe Watch Pro | Wearables | 50 | 45 | 1200 | (formula) | (formula) |
| V102 | Vibe SoundBar X | Audio | 30 | 60 | 2500 | (formula) | (formula) |
| V103 | Vibe Hub Mini | Smart Home | 100 | 20 | 450 | (formula) | (formula) |

**Use for**: Task 10 (Stock = Quantity - Sales, IF reorder). Only 3 products here, but Task may want this formula extended.

### Sheet 5: Traffic_Survey (19 × 11)
Dates 2026-04-01 to 2026-04-15, plus 9 columns of traffic counts.
**Use for**: Task 8 or another Excel task (chart?).

## digital_products.docx — **EMPTY (0 bytes)**

Do NOT rely on this file. The `vibe_materials.txt` in U盘 root (separate from rar) contains gadget descriptions used for Task 5.

## Tools Used to Verify

```bash
# Extract rar (no unrar, use 7z)
7z x "IT2 Reassess.rar" -o rar_view -y

# Convert legacy .doc to text (Word can't open .doc headless easily)
soffice --headless --convert-to txt --outdir /tmp/docconv "Assessment 1_Answer Template_Re-Assess Cover.doc"

# Read .accdb (no mdbtools, no sudo, use python)
uv pip install --python /tmp/venv_mdb/bin/python access-parser
python -c "from access_parser import AccessParser; db=AccessParser('vibe_gadgets.accdb'); print(db.parse_table('Smart_Gadgets'))"

# Read .xlsx multi-sheet
python3 -c "from openpyxl import load_workbook; wb=load_workbook('vibe_operations.xlsx', data_only=True); print(wb.sheetnames)"
```

## Field Name Replacements (old skill → real exam)

| Old (Eden) | New (Vibe) |
|---|---|
| `edenplants.mdb` | `vibe_gadgets.accdb` |
| `Eden Garden Centre.xls` | `vibe_operations.xlsx` |
| `Employees.mdb` | `vibe_employees.accdb` |
| Flower table | **Smart_Gadgets** table |
| Flower Code | **Product_Code** |
| Flower Name | **Product_Name** (Hyperlink) |
| Sun/Shade | **Category** (Wearables/Audio/Smart Home) |
| Notes | **User_Manual_Text** |
| Lauderburgh | **Fuzhou / Xiamen / Quanzhou** |
| Lauderburgh (sun) | **Fuzhou/Xiamen** (multiple cities) |
| Task 5 = Flowers | **Task 5 = Smart Gadgets** |