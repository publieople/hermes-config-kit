# XLSX XML Fallback: Read .xlsx without openpyxl

When openpyxl fails (Python 3.14 incompatibility, corrupted styles, etc.),
parse the raw XML inside the xlsx zip archive.

## Full Working Script

```python
import zipfile
import xml.etree.ElementTree as ET

XLSX_NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'

def read_xlsx_raw(filepath):
    """Read xlsx as list of dicts {column_letter: value}, without openpyxl."""
    with zipfile.ZipFile(filepath) as z:
        # 1. String table
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            ss = ET.parse(z.open('xl/sharedStrings.xml'))
            for si in ss.getroot():
                texts = [t.text or '' for t in si.iter(f'{{{XLSX_NS}}}t')]
                strings.append(''.join(texts))

        # 2. Find sheet files
        workbook = ET.parse(z.open('xl/workbook.xml'))
        sheet_files = ['xl/worksheets/sheet1.xml']  # default; could parse workbook for names

        # 3. Parse each sheet
        results = {}
        for sf in sheet_files:
            if sf not in z.namelist():
                continue
            sheet_tree = ET.parse(z.open(sf))
            rows = []
            for row in sheet_tree.findall(f'.//{{{XLSX_NS}}}row'):
                row_data = {}
                for c in row.findall(f'{{{XLSX_NS}}}c'):
                    ref = c.get('r', '')  # e.g., 'A1'
                    col = ''.join(ch for ch in ref if ch.isalpha())
                    v = c.find(f'{{{XLSX_NS}}}v')
                    if v is not None and v.text is not None:
                        if c.get('t') == 's':
                            row_data[col] = strings[int(v.text)]
                        else:
                            row_data[col] = v.text
                if row_data:
                    rows.append(row_data)

            col_set = sorted(set(k for r in rows for k in r),
                           key=lambda c: (len(c), c))
            results[sf] = {'columns': col_set, 'rows': rows}
        return results

# Usage
data = read_xlsx_raw('/tmp/file.xlsx')
for sheet_name, sheet in data.items():
    print(f"{sheet_name}: {len(sheet['rows'])} rows, cols={sheet['columns']}")
    for row in sheet['rows'][:5]:
        vals = [row.get(c, '') for c in sheet['columns']]
        print(' | '.join(str(v)[:30] for v in vals))
```

## Notes

- **Column letters**: The script extracts column letters from cell references (e.g., `'A'` from `'A1'`). If the sheet uses merged cells (rare), only the top-left cell will have data.
- **Date values**: Excel serial date numbers (like `38728`) are stored as-is. Convert with `from datetime import datetime, timedelta; datetime(1899,12,30) + timedelta(days=<n>)`.
- **Multiple sheets**: Parse `xl/workbook.xml` for `<sheet name="..." r:id="..."/>` to get actual sheet names, then follow `xl/_rels/workbook.xml.rels` to resolve `r:id` to sheet file paths.
- **NTFS files**: If the xlsx is on an NTFS mount (`/mnt/c/` or `/mnt/e/`), copy to `/tmp/` first. openpyxl and zipfile both can fail silently on NTFS paths.
