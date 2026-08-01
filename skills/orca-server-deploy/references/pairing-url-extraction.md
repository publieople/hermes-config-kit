# 配对 URL 提取

## 问题

`orca serve --json` 和人类可读输出都会在显示层面截断 base64 配对码（出现 `...`），如：
```
orca://pair?code=eyJ2Ij...ZSJ9
```

完整 URL 在 `orca_server_ready` JSON 里完好，日志文件 `~/.orca/serve.log` 包含。

## 提取命令

```bash
grep orca_server_ready ~/.orca/serve.log | tail -1 | \
  python3 -c "
import sys, json
line = sys.stdin.read()
start = line.index('{\"type\":\"orca_server_ready\"')
end = line.rindex('}') + 1
data = json.loads(line[start:end])
print(data['pairing']['url'])
" > ~/.orca/pairing-url.txt
```

## 验证

配对 URL 包含的 base64 载荷解码后为：
```json
{"v":2,"endpoint":"ws://127.0.0.1:PORT","deviceToken":"...","publicKeyB64":"...","scope":"runtime"}
```

## WSL → Windows 取值

Windows 侧可通过 `\\wsl$\<distro>\home\po\.orca\pairing-url.txt` 直接访问文件。
WSL 终端下直接 `cat ~/.orca/pairing-url.txt`。
