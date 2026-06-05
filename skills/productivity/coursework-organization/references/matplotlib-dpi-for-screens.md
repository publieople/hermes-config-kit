# Matplotlib DPI for Academic Submissions

## Problem
Textbook code often uses `plt.figure(figsize=(10, 6), dpi=600)` — print-quality resolution. This produces a 6000×3600 pixel chart window that overflows the screen. The user complained the chart was "too big, doesn't fit on screen" and needed to re-screenshot.

## Fix
Change to screen-friendly settings:

```python
plt.figure(figsize=(10, 5), dpi=120)  # 1200×600 px — fits any screen
plt.xticks(rotation=30)               # less aggressive tilt
plt.xlabel('标签', fontsize=12)       # smaller fonts
plt.title('标题', fontsize=14)         # smaller title
```

## Why 120 DPI?
- Standard screen DPI is 96-120. 600 DPI is for print.
- At 600 DPI, a 10×6" figure = 6000×3600 px window.
- At 120 DPI, the same figure = 1200×720 px — fits a 1080p display.
