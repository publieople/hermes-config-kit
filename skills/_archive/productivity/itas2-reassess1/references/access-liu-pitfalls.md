# Access + SQL Pitfalls — verified this session

Specific traps that cost time when running SQL inside Microsoft Access (whether pasted into the SQL view of a query, run via VBA, or generated programmatically).

## Reserved-word field names

Field names that look fine but break `INSERT INTO ... (col, col) VALUES (...)` because Access treats them as keywords:

| Field name | Fix |
|---|---|
| `Premium_Line` | Wrap: `[Premium_Line]` — or rename to `IsPremium` |
| `Order` | Wrap: `[Order]` |
| `Date` | Wrap: `[Date]` — extremely common trap |
| `Description` | Sometimes reserved, wrap `[Description]` |
| `Name` | Wrap `[Name]` |
| `User` | Wrap `[User]` |
| `Password` | Wrap `[Password]` |

**Rule**: any field whose name is also an English word → wrap in `[ ]`. Single multi-word names with underscore (like `Premium_Line`) are usually fine; single-word English nouns are usually NOT.

## Booleans in INSERT VALUES

Access uses `True`/`False` for Yes/No fields. Common mistakes:
- ❌ `'Yes'` / `'No'` — string, becomes text
- ❌ `1` / `0` — sometimes works but inconsistent
- ✅ `True` / `False` — works in SQL view
- ✅ `-1` / `0` — works in DAO/ADO but NOT SQL view

## Hyperlink fields

- Display text and URL stored as `"DisplayText#URL#"`. The `#` is the separator.
- In SQL INSERT, supply just the display text or full `"text#url#"` form.
- Hyperlink fields often come pre-populated in source DBs — verify in Access Datasheet View, don't trust parser dumps.

## Currency field quirks

- Display format ≠ stored value. The field stores a numeric, the Format property decides how it's shown.
- access-parser on Linux reads raw bytes and reports inflated values (×1000) for Currency fields formatted as `¥#,##0.00`. Trust Access display, not parser output.

## Table creation in SQL

`SELECT * INTO NewTable FROM SourceTable WHERE 1=0;` copies **structure only** (matches the Access GUI "Paste → Structure Only"). Useful for Task 11.

For data + structure: `SELECT * INTO NewTable FROM SourceTable;`

## Relationship + Query (Task 23 template)

```sql
-- Create relationship programmatically (NOT supported in Access SQL DDL)
-- Must use GUI: Database Tools > Relationships > drag field > Enforce Referential Integrity

-- Then query:
SELECT 
    Staff.Employee_Number, 
    Staff.First_Name, 
    Staff.Last_Name, 
    Overtime_Log.Date_Worked, 
    Staff.Hourly_Rate, 
    [Hourly_Rate]*[Overtime_Hours] AS Earned_Overtime_Pay
FROM Staff 
INNER JOIN Overtime_Log ON Staff.Employee_Number = Overtime_Log.Employee_Number;
```

Note: `AS Earned_Overtime_Pay` works. Without `AS`, Access uses the expression as the column name.

## Properties / Metadata (Task 26)

Cannot be set via SQL. Must use File → Info → Properties → Advanced Properties dialog. Or programmatically via VBA `Application.SetProperty`.

Minimum to fill: Author + Comments. Title/Subject/Keywords are bonus.

## File-permissions copy from Linux to NTFS

`shutil.copy(src, dst)` fails on NTFS-mounted dirs with `PermissionError` because it tries to preserve POSIX mode bits. Use `shutil.copyfile(src, dst)` which skips metadata copy. Confirmed working on `/mnt/e/` WSL mounts.

## WSL /mnt/e drops to I/O errors

After heavy Access usage on Windows side, the 9P share can hang — `ls /mnt/e` returns I/O error. Fix: from Windows, run `wsl --shutdown` in PowerShell, then re-open WSL. Do NOT try to remount from inside WSL — won't work. Avoid by disabling OneDrive sync on E:\ during exam.