# Template Filling: Multi-Run Pitfall

## The Problem

When a docx paragraph has blanks (`_____`) split across multiple `<w:r>` elements (runs), you CANNOT fill them by:

1. Reading `paragraph.text` to get the full text
2. Searching for `_____` patterns in the full text
3. Replacing inside individual runs

**Why this fails:** The positional mapping between the concatenated paragraph text and individual runs is fragile. A `_____` that appears in position N of the full text may span across a run boundary, or the first `_____` in the full text may not be in the first run. The `fill_blank()` pattern of "find blank in full text → find which run contains it → replace" is unreliable.

## The Solution: Run-Indexed Replacement

Inspect the template with run-level granularity FIRST:

```python
for i, run in enumerate(para.runs):
    if run.text.strip():
        print(f"Run[{i}]: '{run.text[:80]}'")
```

Then target each blank by its exact `(paragraph_index, run_index)`:

```python
# Para [14], Run[3] has: "T.RandomHorizontalFlip(p=_____)"
doc.paragraphs[14].runs[3].text = re.sub(
    r'_{3,}', '0.5', doc.paragraphs[14].runs[3].text, count=1
)
```

For runs with multiple blanks, replace in order:

```python
def replace_underscores(text, *answers):
    """Replace consecutive _____ patterns in order."""
    for ans in answers:
        text = re.sub(r'_{3,}', str(ans), text, count=1)
    return text
```

## Verify Before Delivering

After filling, ALWAYS run a verification pass checking that:
1. Every expected value appears in its paragraph
2. NO `_{3,}` patterns remain anywhere (paragraphs AND table cells)

```python
checks = {
    14: ['0.5', '0.2', '224', '0.456', '0.225'],
    27: ['samples[idx]', 'Image.open(img_path)', 'self.transform(img)', "'int64'"],
}
for idx, keywords in checks.items():
    text = doc.paragraphs[idx].text
    for kw in keywords:
        if kw not in text:
            print(f"❌ [{idx}] missing: '{kw}'")
```

## The "Don't Fabricate" Principle

When filling task books or forms, NEVER make up values for inapplicable sections:

- **Leave empty**: Fields like IP address, firmware version, battery percentage when using simulator mode
- **Mark N/A**: Use "N/A (模拟器模式)" or "无" instead of inventing numbers
- **Don't assume**: Group numbers, bonus scores, teacher ratings — leave blank or use the template default

The user can always fill in what they know later. Fabricated data is worse than empty fields — it creates false records that may be submitted as real.
