# Image Embedding: python-docx Bug & XML Workaround

## The Problem

`python-docx`'s `run.add_picture()` is unreliable when editing existing documents:
- The **relationship** (rId → media/image.png) IS added to `word/_rels/document.xml.rels`
- The **image file** IS written to `word/media/`
- But the **`<w:drawing>` element** is NOT always written to `word/document.xml`

Result: file size grows (image IS in zip), but the image doesn't render. `python-docx` reports `Images: 1` through its rels API but the XML reference is missing.

## The Reliable Solution: XML-Level Editing

### Step 1: Unpack

```python
import zipfile, shutil, os
with zipfile.ZipFile('document.docx') as zf:
    zf.extractall('/tmp/unpacked/')
```

### Step 2: Copy images + add rels

```python
shutil.copy('screenshot.png', '/tmp/unpacked/word/media/screenshot.png')

import re
rels_path = '/tmp/unpacked/word/_rels/document.xml.rels'
with open(rels_path) as f:
    rels = f.read()
rids = [int(m.group(1)) for m in re.finditer(r'rId(\d+)', rels)]
new_rid = f'rId{max(rids) + 1}'
rels = rels.replace('</Relationships>',
    f'<Relationship Id="{new_rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/screenshot.png"/></Relationships>')
with open(rels_path, 'w') as f:
    f.write(rels)
```

### Step 3: Insert `<w:drawing>` into document.xml

Use regex to find the placeholder and insert before `</w:p>`:

```python
drawing = f'''<w:r><w:rPr><w:noProof/></w:rPr><w:drawing>
  <wp:inline distT="0" distB="0" distL="0" distR="0" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">
    <wp:extent cx="5029200" cy="3762375"/>
    <wp:docPr id="1" name="img"/>
    <a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
      <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
        <pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
          <pic:nvPicPr><pic:cNvPr id="0" name="img"/><pic:cNvPicPr/></pic:nvPicPr>
          <pic:blipFill><a:blip r:embed="{new_rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
          <pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="5029200" cy="3762375"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>
        </pic:pic>
      </a:graphicData>
    </a:graphic>
  </wp:inline>
</w:drawing></w:r>'''

with open('/tmp/unpacked/word/document.xml') as f:
    xml = f.read()
# Match <w:t>PLACEHOLDER</w:t> ... </w:p>, insert drawing before </w:p>
pattern = r'(<w:t[^>]*>\[PLACEHOLDER TEXT\]</w:t>.*?)(</w:p>)'
xml = re.sub(pattern, r'\1' + drawing + r'\2', xml, count=1, flags=re.DOTALL)
with open('/tmp/unpacked/word/document.xml', 'w') as f:
    f.write(xml)
```

### Step 4: Repack

```python
os.remove('document.docx')
shutil.make_archive('document', 'zip', '/tmp/unpacked/')
shutil.move('document.zip', 'document.docx')
```

## Verification

```python
with zipfile.ZipFile('document.docx') as zf:
    xml = zf.read('word/document.xml').decode()
    assert new_rid in xml, f'{new_rid} NOT in document.xml!'
```

## EMU Sizing

- 1 inch = 914,400 EMU
- 5.5" wide = 5,029,200 EMU (fits document width with margins)
- Exact values not critical — Word scales to fit

## Pitfalls

- **Unique rIds**: Each image needs its own rId. Scan existing rels first.
- **Cleanup old failures**: `re.sub(r'<w:drawing>.*?</w:drawing>', '', xml, flags=re.DOTALL)` removes broken insertions.
- **Complex formatting**: Placeholder text may have `<w:rPr>` with fonts/colors — use `.*?` + `re.DOTALL` to span across runs.
- **Content types**: Verify `[Content_Types].xml` has `<Default Extension="png" ContentType="image/png"/>`.
