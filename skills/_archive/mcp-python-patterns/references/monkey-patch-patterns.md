# Monkey-Patch Patterns for Python MCP Bridges

## Problem: Import-time Reference Capture

When a library does `from requests import get`, it captures the function reference at import time. Patching `requests.get` later has no effect on the library's internal reference.

### Detection

If your monkey-patch "doesn't work" despite correct code, check:

```python
import target_pkg.utils
print(target_pkg.utils.get)  # <function get at 0x...> — local reference
```

### Fix 1: Patch the actual reference

```python
import target_pkg.utils
orig = target_pkg.utils.get
def patched(url, **kw):
    kw.setdefault('verify', False)
    return orig(url, **kw)
target_pkg.utils.get = patched
```

### Fix 2: For module-level constants (strings)

```python
# Module A:
from . import BASE_URL  # string, immutable, captured at import

# Patch ALL modules that import it:
import pkg.extractors, pkg.extractors.search, pkg.extractors.download
new_url = os.environ.get("BASE_URL_OVERRIDE")
pkg.extractors.BASE_URL = new_url
pkg.extractors.search.BASE_URL = new_url
pkg.extractors.download.BASE_URL = new_url
```

## Problem: Clash MITM Proxy + SSL Verify

Clash on Windows (WSL2 host, localhost:7890) intercepts HTTPS with MITM certificates. Python's `requests` + `certifi` fails SSL verification when traffic goes through Clash.

### Fix

```python
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Then patch the library's actual `get` reference (see above)
# Pass verify=False in the patched function
```

Gate behind an env var so it's opt-in:

```python
if os.environ.get("SKIP_SSL_VERIFY", "").lower() in ("1", "true", "yes"):
    # apply patch
```

Then register with `hermes mcp add --env SKIP_SSL_VERIFY=1`.

## Hermes MCP Env Var Passing

When `hermes mcp add` asks for env vars, they are passed to the subprocess. The native-mcp skill's env filtering applies: only explicit `--env` vars + baseline vars reach the server.

```bash
hermes mcp add myserver \
  --command python3 \
  --args /path/to/server.py \
  --env HTTP_PROXY=http://127.0.0.1:7890 HTTPS_PROXY=http://127.0.0.1:7890
```

To update env vars for an existing server: remove and re-add. No in-place edit command exists.
