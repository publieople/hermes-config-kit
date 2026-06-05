# Archive Inspection Fallback Techniques

> Absorbed from `document-inspection` skill (archived). Zero-dependency techniques for inspecting common document formats using Python stdlib and 7z.

## When to Use

The standard tools (`python -m markitdown`, LibreOffice, `python-pptx`, `python-docx`) are preferred when available. Use these fallback techniques when they aren't installed.

## PPTX (PowerPoint) — Python zipfile (already covered in main skill)

A .pptx file is a ZIP archive containing slide XML files. No extra packages needed. See the main `coursework-organization` SKILL.md for the full technique.

## DOCX (Word) — Python zipfile

```bash
python3 -c "
import zipfile, xml.etree.ElementTree as ET

with zipfile.ZipFile('document.docx') as z:
    xml_content = z.read('word/document.xml')
    root = ET.fromstring(xml_content)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    texts = [t.text for t in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if t.text]
    print('\\n'.join(texts))
"
```

## RAR — 7z CLI

Use `7z` (from p7zip) when `unrar` isn't installed:

| Command | Description |
|---------|-------------|
| `7z l archive.rar` | List contents |
| `7z e archive.rar -o/tmp/out -y` | Extract all |
| `7z e archive.rar -o/tmp/out -y "path/inside/file.py"` | Extract specific file |

Check with `command -v 7z`.

## ZIP — Python zipfile

```bash
python3 -c "
import zipfile
with zipfile.ZipFile('archive.zip') as z:
    for name in z.namelist():
        print(name, f'(size: {z.getinfo(name).file_size} bytes)')
"
```

## Limitations

- PPTX extraction just grabs `<a:t>` text elements — no formatting, images, charts, or embedded objects
- DOCX extraction similarly loses all formatting
- RAR via 7z requires `7z` installed
- No markdown conversion, no table detection, no image analysis

For richer extraction, install `python -m pip install markitdown[pptx]` or use LibreOffice.
