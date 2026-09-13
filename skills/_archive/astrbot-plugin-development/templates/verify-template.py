"""ad-hoc verification for astrbot_plugin_<NAME> v<VERSION>.

validates (no permanent tests):
1. metadata.yaml parses + required fields
2. _conf_schema.json parses + N expected fields + correct defaults
3. main.py syntax
4. decorators: @register (on class), @command("..."), @llm_tool(name="...")
5. class + method names match expectation
6. machinery strings present in source (cooldown, http client, etc.)
7. live external API call (use urllib for compat)
8. algorithm simulation (cooldown, parser, etc.)
9. repo hygiene: requirements.txt, .gitignore, no stray scripts

Run with the venv that has the plugin's deps:
    ~/.local/share/uv/tools/astrbot/bin/python3 /tmp/hermes-verify-<name>.py

NOT a test suite. Delete after passing. State as "ad-hoc verification".
"""

import ast
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

PLUGIN = "/home/po/astrbot/data/plugins/astrbot_plugin_<NAME>"

ok = True
def chk(label, cond, detail=""):
    global ok
    mark = "OK  " if cond else "FAIL"
    print(f"  [{mark}] {label}" + (f" -- {detail}" if detail else ""))
    ok &= cond


# === metadata.yaml ===
print("== metadata.yaml ==")
try:
    import yaml
except ImportError:
    yaml = None
    print("  [WARN] pyyaml missing")
if yaml:
    md = yaml.safe_load(Path(f"{PLUGIN}/metadata.yaml").read_text(encoding="utf-8"))
    chk("name", md.get("name") == "astrbot_plugin_<NAME>", str(md.get("name")))
    chk("version", md.get("version") == "v<VERSION>", str(md.get("version")))
    # author / repo checks ...


# === _conf_schema.json ===
print("== _conf_schema.json ==")
sch = json.loads(Path(f"{PLUGIN}/_conf_schema.json").read_text(encoding="utf-8"))
expected = {<list of expected field keys>}
chk("schema fields", expected <= set(sch.keys()), f"missing={expected - set(sch.keys())}")
# default checks per field ...


# === main.py ===
print("== main.py ==")
src = Path(f"{PLUGIN}/main.py").read_text(encoding="utf-8")
tree = ast.parse(src)
chk("syntax parses", True)

# Walk FunctionDef AND ClassDef (the @register lives on the class)
reg = cmd = llm = False
for n in ast.walk(tree):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        for d in n.decorator_list:
            if isinstance(d, ast.Call) and isinstance(d.func, ast.Name):
                arg = None
                if d.args and isinstance(d.args[0], ast.Constant):
                    arg = d.args[0].value
                elif d.keywords:
                    for kw in d.keywords:
                        if isinstance(kw.value, ast.Constant):
                            arg = kw.value.value
                            break
                if d.func.id == "register": reg = True
                if d.func.id == "command" and arg == "<CMD>": cmd = True
                if d.func.id == "llm_tool" and arg == "<TOOL>": llm = True

chk("@register", reg)
chk('@command("<CMD>")', cmd)
chk('@llm_tool("<TOOL>")', llm)

class_node = next((n for n in tree.body if isinstance(n, ast.ClassDef)), None)
chk("class <Name>", class_node is not None and class_node.name == "<Name>")
methods = [m.name for m in (class_node.body if class_node else []) if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
for m in [<list of method names>]:
    chk(f"method {m}", m in methods)


# === machinery strings ===
# chk("uses time.time()", "time.time()" in src)
# chk("uses event.unified_msg_origin", "unified_msg_origin" in src)
# chk("API endpoint string", "<api host>" in src)
# ... adapt to the plugin ...


# === repo hygiene (BEFORE writing any temp artifacts) ===
print("== repo hygiene ==")
stray = ["/tmp/hermes-test-<name>.py", "/tmp/hermes-verify-<name>.py"]
this_script = os.path.abspath(__file__)
for s in stray:
    s_abs = os.path.abspath(s)
    if s_abs == this_script:
        chk(f"is self", True)
    else:
        chk(f"no leftover {os.path.basename(s)}", not os.path.exists(s))
chk("requirements.txt has <dep>", "<dep>" in Path(f"{PLUGIN}/requirements.txt").read_text())
chk(".gitignore covers __pycache__", "__pycache__" in Path(f"{PLUGIN}/.gitignore").read_text())


# === live API call (if plugin uses one) ===
# print("== live API call ==")
# try:
#     with urllib.request.urlopen(urllib.request.Request("<url>", method="GET"), timeout=20) as r:
#         body = json.loads(r.read())
#         chk("HTTP 200", r.status == 200)
#         # ...
# except Exception as e:
#     chk("live API", False, f"{type(e).__name__}: {e}")


# === algorithm simulation (cooldown, parser, etc.) ===
# def check(...): ...
# ...


print()
print(f"result: {'ALL OK' if ok else 'FAILED'}")
sys.exit(0 if ok else 1)
