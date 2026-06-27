# Repacking DOCX with Python's zipfile (no defusedxml/pack.py needed)

When `pack.py` is unavailable (missing `defusedxml` module), use Python's built-in `zipfile`:

```python
import zipfile, os

src = '/tmp/docx_unpacked'
dst = 'output.docx'

with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(src):
        for f in files:
            full = os.path.join(root, f)
            arcname = os.path.relpath(full, src)
            zf.write(full, arcname)

# Verify image reference survived
with zipfile.ZipFile(dst) as zf:
    xml = zf.read('word/document.xml').decode()
    assert 'rId9' in xml, 'Image reference missing!'
```

**Shell fallback:** `unzip` for unpacking, `zip -r` for repacking — but note that `zip` may not be installed in minimal WSL environments. Use Python's `zipfile` as the reliable cross-platform approach.
