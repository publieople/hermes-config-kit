# Extracting Text from PPTX Slides (without python-pptx)

A PPTX file is a ZIP archive containing XML files. Each slide is stored as `ppt/slides/slideN.xml`. Text content lives inside `<a:t>` elements.

## One-liner (shell)

```bash
python3 -c "
import zipfile, re, sys
with zipfile.ZipFile(sys.argv[1]) as z:
    slides = sorted(f for f in z.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml'))
    for i, s in enumerate(slides, 1):
        text = ' '.join(re.findall(r'<a:t[^>]*>([^<]+)</a:t>', z.read(s).decode('utf-8')))
        if text.strip(): print(f'--- Slide {i} ---\n{text}\n')
" 演示文稿.pptx
```

## Python snippet (for embedding in code)

```python
import zipfile, re

def extract_pptx_text(path: str, max_slides: int = 50) -> list[dict]:
    """Extract slide titles and text content from a .pptx file.
    
    Returns list of {slide_num: int, text: str} dicts.
    """
    with zipfile.ZipFile(path) as z:
        slides = [
            f for f in z.namelist()
            if f.startswith('ppt/slides/slide') and f.endswith('.xml')
        ]
        slides.sort()
        
        results = []
        for i, slide_path in enumerate(slides[:max_slides], 1):
            content = z.read(slide_path).decode('utf-8')
            texts = re.findall(r'<a:t[^>]*>([^<]+)</a:t>', content)
            text = ' '.join(texts).strip()
            if text:
                results.append({"slide_num": i, "text": text})
        return results
```

## Notes

- Works on any platform (no binary dependencies)
- Only extracts text — no images, shapes, or layout info
- `<a:t>` elements can span multiple lines; the regex captures inner text only
- For Japanese/Korean/emoji content, the UTF-8 encoding handles it natively
- Slide numbering is 1-indexed matching PowerPoint's slide sorter
