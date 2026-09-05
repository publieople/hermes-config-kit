#!/usr/bin/env python3
"""AST 装饰器检查 — 不依赖 AstrBot runtime 也能用。

检查 main.py 里注册的 @command / @llm_tool / @register 装饰器及参数,
确认插件骨架合规。

用法:
  python3 check_plugin.py <plugin_dir>
  python3 check_plugin.py ~/astrbot/data/plugins/astrbot_plugin_Pic

退出码:0=全过, 1=有失败。
"""
import ast
import json
import sys
from pathlib import Path


def check_decorators(plugin_dir: Path) -> bool:
    main_py = plugin_dir / "main.py"
    if not main_py.exists():
        print(f"FAIL: {main_py} not found")
        return False

    src = main_py.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        print(f"FAIL: main.py syntax error: {e}")
        return False

    # 收集所有装饰器
    items = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in node.decorator_list:
                name = None
                arg = None
                if isinstance(d, ast.Call):
                    if isinstance(d.func, ast.Attribute):
                        name = d.func.attr
                    elif isinstance(d.func, ast.Name):
                        name = d.func.id
                    if d.args and isinstance(d.args[0], ast.Constant):
                        arg = d.args[0].value
                    elif d.keywords and isinstance(d.keywords[0].value, ast.Constant):
                        arg = d.keywords[0].value.value
                elif isinstance(d, ast.Name):
                    name = d.id
                items.append((node.name, name, arg))

    # 至少要有 @register
    has_register = any(dec == "register" for _, dec, _ in items)
    if not has_register:
        print("FAIL: no @register decorator (plugin won't load)")
        return False

    # @llm_tool 必须有 docstring + Args
    for fn_name, dec, _ in items:
        if dec == "llm_tool":
            # 找函数定义拿 docstring
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == fn_name:
                    doc = ast.get_docstring(node) or ""
                    if "Args:" not in doc:
                        print(f"WARN: llm_tool '{fn_name}' missing 'Args:' in docstring (LLM won't know params)")
                    elif "(string)" not in doc and "(number)" not in doc and "(boolean)" not in doc:
                        print(f"WARN: llm_tool '{fn_name}' has Args: but no type tags")

    # 打印所有装饰器
    print(f"\nDecorators in {main_py.name}:")
    for fn, dec, arg in items:
        arg_str = repr(arg) if arg is not None else ""
        print(f"  {fn:35s} @{dec:25s} {arg_str}")

    return True


def check_json(plugin_dir: Path) -> bool:
    schema = plugin_dir / "_conf_schema.json"
    if not schema.exists():
        print(f"\nWARN: {schema.name} missing — config will be None")
        return True  # 不是错,是可选
    try:
        json.loads(schema.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"FAIL: _conf_schema.json invalid: {e}")
        return False
    print(f"\nOK: _conf_schema.json is valid JSON")
    return True


def check_metadata(plugin_dir: Path) -> bool:
    meta = plugin_dir / "metadata.yaml"
    if not meta.exists():
        print(f"FAIL: {meta.name} missing (AstrBot requires this)")
        return False
    try:
        import yaml
        d = yaml.safe_load(meta.read_text(encoding="utf-8"))
    except ImportError:
        # 没 yaml,用基础解析
        d = {}
        for line in meta.read_text(encoding="utf-8").splitlines():
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                d[k.strip()] = v.strip()
    except Exception as e:
        print(f"FAIL: metadata.yaml parse error: {e}")
        return False

    required = ["name", "version", "author", "desc"]
    missing = [k for k in required if k not in d]
    if missing:
        print(f"FAIL: metadata.yaml missing fields: {missing}")
        return False
    if not d["name"].startswith("astrbot_plugin_"):
        print(f"FAIL: name {d['name']!r} must start with 'astrbot_plugin_'")
        return False
    if not d["version"].startswith("v"):
        print(f"WARN: version {d['version']!r} should start with 'v' (e.g. v1.0.0)")
    print(f"\nOK: metadata.yaml — name={d['name']} version={d['version']} author={d['author']}")
    return True


def main():
    if len(sys.argv) < 2:
        # 默认检查 ~/astrbot/data/plugins/*/main.py
        plugins_dir = Path.home() / "astrbot" / "data" / "plugins"
        if not plugins_dir.is_dir():
            print("usage: check_plugin.py <plugin_dir>")
            sys.exit(1)
        targets = [p for p in plugins_dir.iterdir() if (p / "main.py").exists()]
    else:
        targets = [Path(sys.argv[1])]

    all_ok = True
    for t in targets:
        if not t.is_dir():
            print(f"FAIL: {t} is not a directory")
            all_ok = False
            continue
        print(f"\n{'='*60}\nChecking: {t}\n{'='*60}")
        ok = check_metadata(t) and check_decorators(t) and check_json(t)
        if not ok:
            all_ok = False

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
