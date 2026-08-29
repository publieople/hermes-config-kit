# xlsx → Markdown via Raw XML Extraction

## When to use

When openpyxl (or any xlsx reader) throws `Fill() takes no arguments` — a known compatibility issue with certain Excel-generated `.xlsx` files on Python 3.12+.

## How it works

`.xlsx` is a ZIP archive containing XML files. Extract and parse directly:

```bash
# 1. Unzip
mkdir -p /tmp/xl && cd /tmp/xl
unzip -o /path/to/file.xlsx

# 2. Read shared strings
python3 -c "
import xml.etree.ElementTree as ET
ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
tree = ET.parse('xl/sharedStrings.xml')
strings = []
for si in tree.getroot():
    texts = [t.text or '' for t in si.iter(f'{{{ns}}}t')]
    strings.append(''.join(texts))
print(f'Loaded {len(strings)} strings')
"

# 3. Parse sheet data
python3 -c "
import xml.etree.ElementTree as ET
ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
ss = ET.parse('xl/sharedStrings.xml')
strings = [''.join(t.text or '' for t in si.iter(f'{{{ns}}}t')) for si in ss.getroot()]
sheet = ET.parse('xl/worksheets/sheet1.xml')
for row in sheet.findall(f'.//{{{ns}}}row'):
    vals = {}
    for c in row.findall(f'{{{ns}}}c'):
        col = ''.join(ch for ch in c.get('r') if ch.isalpha())
        v = c.find(f'{{{ns}}}v')
        if v is not None and v.text:
            vals[col] = strings[int(v.text)] if c.get('t') == 's' else v.text
    if vals:
        print(vals)
"
```

## Excel Serial Date Conversion

Excel stores dates as serial numbers (days since 1899-12-30):

```python
from datetime import datetime, timedelta

def excel_serial_to_date(serial):
    s = int(float(serial))
    if s < 60:  # before 1900-02-29, unreliable
        return None
    return (datetime(1899, 12, 30) + timedelta(days=s)).strftime('%Y-%m-%d')
```

## Structuring for RAG

Each entity should be a self-contained chunk with clear field labels:

```markdown
## 姓名
- **昵称**: xxx
- **QQ**: xxx
- **性别**: xxx
- **生日**: YYYY-MM-DD
- **是否在群**: 是/否
- **去向**: city
- **位置/学校**: university
- **专业**: major
- **电话**: xxx
- **备注/XP**: xxx
```

Separate entries with `---` to ensure chunk boundaries. AstrBot's chunker with `chunk_size=512` and `chunk_overlap=50` will preserve entry boundaries if each entry is ~200 chars.
