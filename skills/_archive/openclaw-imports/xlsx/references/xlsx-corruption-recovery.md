# XLSX Corruption Recovery

When `openpyxl` `wb.save()` fails mid-write (e.g., due to a Python exception during pivot table creation, chart serialization, or style writing), the resulting file can be a **partial zip archive** missing critical XML files. The file will report as "Microsoft Excel 2007+" to `file` command but fail to open in Excel/LibreOffice/openpyxl.

## Missing files (typical corruption pattern)

After a failed save, these files are commonly missing:
- `[Content_Types].xml` — content type registry (MANDATORY)
- `_rels/.rels` — root relationships (MANDATORY)
- `xl/workbook.xml` — sheet definitions (MANDATORY)
- `xl/_rels/workbook.xml.rels` — workbook relationships (MANDATORY)
- `xl/styles.xml` — cell style definitions (needed if sheets reference styles)
- `xl/sharedStrings.xml` — shared string table (only if sheets use `t="s"` cells)

## Recovery procedure

### Step 1: Extract surviving files
```bash
mkdir recover && cd recover
python3 -c "
import zipfile
with zipfile.ZipFile('/path/to/corrupted.xlsx', 'r') as z:
    z.extractall('.')
"
```

### Step 2: Identify what survives
Sheet XML files (`xl/worksheets/sheet*.xml`) typically survive intact. Focus on these.

### Step 3: Reconstruct `[Content_Types].xml`
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <!-- Add one Override per existing sheet -->
  <Override PartName="/xl/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
```

### Step 4: Reconstruct `_rels/.rels`
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
```

### Step 5: Reconstruct `xl/workbook.xml`
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="SheetName1" sheetId="1" r:id="rId1"/>
    <sheet name="SheetName2" sheetId="2" r:id="rId2"/>
  </sheets>
</workbook>
```

### Step 6: Reconstruct `xl/_rels/workbook.xml.rels`
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
</Relationships>
```

### Step 7: Reconstruct `xl/styles.xml` (if sheets reference style IDs)
Find all style IDs used in sheets: `grep -oP 's="\d+"' xl/worksheets/*.xml | sort -t'"' -k2 -n | uniq`
Create a styles.xml with `cellXfs count="N+1"` where N is the highest style ID found.
Minimal template with 28 cellXfs (covers IDs 0-27):
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="3">
    <font><sz val="11"/><name val="宋体"/></font>
    <font><sz val="11"/><name val="宋体"/><b/></font>
    <font><sz val="14"/><name val="宋体"/><b/></font>
  </fonts>
  <fills count="3">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFC7CE"/></patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border><left style="thin"><color auto="1"/></left><right style="thin"><color auto="1"/></right><top style="thin"><color auto="1"/></top><bottom style="thin"><color auto="1"/></bottom><diagonal/></border>
  </borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="28">
    <!-- 28 identical xf entries, fill in as needed -->
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <!-- ... repeat for count -->
  </cellXfs>
  <cellStyles count="1">
    <cellStyle name="Normal" xfId="0" builtinId="0"/>
  </cellStyles>
  <dxfs count="2">
    <dxf><fill><patternFill><bgColor rgb="FFFFC7CE"/></patternFill></fill></dxf>
    <dxf><fill><patternFill patternType="solid"><bgColor rgb="FFFFC7CE"/></patternFill></fill></dxf>
  </dxfs>
</styleSheet>
```

### Step 8: Clean up leftover references
If the partial save included references to non-existent files (charts, drawings):
- Check `xl/worksheets/_rels/sheet1.xml.rels` for drawing/chart references
- Remove any `<Relationship>` pointing to non-existent files
- Remove corresponding `<Override>` entries from `[Content_Types].xml`
- Remove `<drawing r:id="..."/>` from sheet XML

### Step 9: Repack
```bash
cd recover && rm -f /path/to/recovered.xlsx
python3 -c "
import zipfile, os
with zipfile.ZipFile('/path/to/recovered.xlsx', 'w', zipfile.ZIP_DEFLATED) as zout:
    for root, dirs, files in os.walk('.'):
        for f in files:
            path = os.path.join(root, f)
            zout.write(path, path[2:])
"
```

### Step 10: Verify with openpyxl
```python
from openpyxl import load_workbook
wb = load_workbook('/path/to/recovered.xlsx')
print(wb.sheetnames)
```

## Prevention

**Always copy the original file before running openpyxl modifications.** If `wb.save()` raises an exception, the original is safe and you can retry.
