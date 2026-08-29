# Running OpenCV scripts headless (WSL / CI / no display)

When a script uses `cv2.imshow()` / `cv2.waitKey()` / `cv2.destroyAllWindows()`
and you have no X11 display, apply these overrides BEFORE the script loads:

## Method 1: Environment variable + monkey-patch (Python)

```python
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

import cv2
cv2.imshow = lambda *a, **kw: None
cv2.waitKey = lambda *a, **kw: -1
cv2.destroyAllWindows = lambda *a, **kw: None
```

## Method 2: Handle `input()` prompts in non-interactive scripts

Scripts that call `input()` will raise `EOFError` in non-interactive mode:

```python
import builtins
builtins.input = lambda prompt='': 'n'  # auto-answer 'n' to all prompts

# Or: cycle through specific answers
responses = iter(['', '', 'n'])
builtins.input = lambda p='': next(responses, 'n')
```

## Method 3: Use `runpy` when `exec()` lacks `__file__`

Some scripts reference `__file__` (e.g., `os.path.dirname(__file__)`).
Using `exec(open(...).read())` won't define `__file__`. Use `runpy` instead:

```python
import sys, runpy
sys.argv = ['script_name', '--flag']
runpy.run_path('script.py', run_name='__main__')
```

## Method 4: Timeout for infinite loops

Real-time vision systems run until a keypress. Use `timeout` to cap:

```bash
timeout 8 python3 script.py  # SIGTERM after 8 seconds
```
