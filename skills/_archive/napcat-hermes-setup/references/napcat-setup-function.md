# hermes_cli/gateway.py — _setup_napcat() 完整函数

合并 MoeOver/main 后此函数会丢失，需手动加回。

## 位置

在 `_setup_qqbot()` 函数定义和 `_setup_signal()` 函数定义之间（约 ~5490 行）。

## 完整代码

```python
def _setup_napcat():
    """Interactive setup for NapCat (OneBot 11 reverse WebSocket)."""
    print()
    print(color("  ─── 🐱 NapCat Setup ───", Colors.CYAN))
    print()
    print_info("NapCat connects TO Hermes via reverse WebSocket.")
    print_info("You need NapCatQQ running on the machine with QQ.")
    print_info("See: https://github.com/NapNeko/NapCatQQ")
    print()

    existing_token = get_env_value("NAPCAT_TOKEN")
    if existing_token:
        print_success("NapCat is already configured.")
        print_info(f"  Token: {existing_token[:8]}...")
        if not prompt_yes_no("  Reconfigure NapCat?", False):
            return
        print()

    import secrets
    default_token = existing_token or secrets.token_hex(16)
    token = input(f"  Shared token (for WS auth) [{default_token[:16]}...]: ").strip() or default_token
    if token:
        save_env_value("NAPCAT_TOKEN", token.strip())

    host = input("  Listen host [0.0.0.0]: ").strip() or "0.0.0.0"
    save_env_value("NAPCAT_HOST", host)

    port = input("  Listen port [8646]: ").strip() or "8646"
    save_env_value("NAPCAT_PORT", port)

    path = input("  WebSocket path [/napcat/ws]: ").strip() or "/napcat/ws"
    save_env_value("NAPCAT_PATH", path)

    save_env_value("NAPCAT_ENABLED", "true")

    home_channel = input("  Your QQ number (home channel): ").strip()
    if home_channel:
        save_env_value("NAPCAT_HOME_CHANNEL", home_channel)

    if prompt_yes_no("  Allow all users in groups to interact?", True):
        save_env_value("NAPCAT_ALLOW_ALL_USERS", "true")
    else:
        allowed = input("  Comma-separated QQ numbers to allow: ").strip()
        if allowed:
            save_env_value("NAPCAT_ALLOW_FROM", allowed)

    print()
    print_success("🐱 NapCat configured!")
```

## PLATFORMS dict 条目

在 `_PLATFORMS` dict 中（~5647 行），`"qqbot": _setup_qqbot,` 之后加：

```python
        "napcat": _setup_napcat,
```

## 注意事项

- 函数内使用 `input()` 而非不存在的 `prompt_input()`。其他 setup 函数也是用 `input()`。
- `get_env_value`、`save_env_value`、`prompt_yes_no`、`print_success`、`print_info`、`color`、`Colors` 等辅助函数是文件级别定义的，直接使用即可。
