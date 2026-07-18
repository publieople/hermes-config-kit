# WSL → Windows NTFS 大文件传输

## 症状

在 WSL 里 `cp <大文件> /mnt/<c|e|d>/<...>` 写 Windows NTFS 挂载盘时：

- `cp` 命令 **静默截断**（写一半停掉，文件大小停在某个值）
- `cp` 看似完成（exit 0）但目标文件缺失 / 长度为 0
- `cp` 进 `terminal(background=true)` 后 uptime 158s 退出但**目标文件根本没创建**（`echo "DONE" > log` 那行都没跑到）
- 用 `stat`/`ls` 看目标文件：**不存在**，但 `cp` 进程已经结束

典型规模：>50MB 单文件，或者 100+ 个小文件目录。

## 根因

WSL2 用 9P 协议把 NTFS 挂载到 `/mnt/<drive>/`，**大文件写操作不稳定**。这跟 venv 权限问题是同一类（NTFS 不支持 Linux 文件权限/IO 模型），但症状更隐蔽——直接 IO 失败但进程不报错。

实测规模：
- `cp 240MB 单文件` → 失败概率高
- `cp -r 1.5GB 目录` → 失败概率高
- `cp 16KB 小文件` → 正常

## 解决方案（按推荐度）

### 1. PowerShell 用 SMB 路径访问 WSL 文件（最稳）

PowerShell 通过 `\\wsl.localhost\<distro>\<path>` 直接读 WSL 文件，由 Windows 文件系统 API 写入目标盘。**完全绕开 WSL2 的 9P 写入层**。

```powershell
# 关键：distro name 用 `wsl.exe -l -v` 查（不是 wsl --status 报的"默认发行版"）
#    用户的 distro name 是 `archlinux`，不是 `Arch`（大写 A 找不到）

\\wsl.localhost\archlinux\home\po\spc\output_server_pack.zip
\\wsl$\archlinux\home\po\spc\output_server_pack.zip   # 旧路径，可能不行
```

拷贝示例（PowerShell）：

```powershell
$src = '\\wsl.localhost\archlinux\home\po\spc\output_server_pack.zip'
$dst = 'C:\Users\po\Downloads\Chapter3_ServerPack.zip'
if (-not (Test-Path $src)) { Write-Host 'src miss'; exit 1 }
$srcSize = (Get-Item $src).Length
Copy-Item -Path $src -Destination $dst -Force
$dstSize = (Get-Item $dst).Length
Write-Host "size match = $(if ($srcSize -eq $dstSize){'OK'}else{'MISMATCH'})"
# size match = OK
```

实测：240MB zip 完整拷到 `C:\Users\po\Downloads\` 一次成功，源/目标 size 完全一致。

### 2. 验证 distro 名字（必走的第一步）

```bash
wsl.exe -l -v
# 输出例：
#   NAME            STATE    VERSION
# * archlinux       Running  2
#   docker-desktop  Running  2
```

PowerShell 路径里的 distro 段必须用这个 NAME 字段。常见错误：
- 用户报告"默认是 Ubuntu"——这是 `wslconfig /setdefault` 的设置，但**实际 distro 名字还是安装时起的那个**（小写、`wsl --list --all` 看到的）
- 区分大小写：`\\wsl$\Arch\...`（大写 A）通常 404

### 3. 反向：Windows → WSL 拷文件

走同一 SMB 路径，PowerShell 用 `Copy-Item` 反向拷也行，或者直接在 WSL 里 `cp /mnt/c/...` 读 Windows 盘（**读比写稳很多**，主要坑是写）。

### 4. zip 优先于目录

如果是要把整个产物传出去，**先在 WSL 打成单个 zip 再传输**，比 `cp -r` 1000+ 个小文件靠谱：

```bash
# 在 WSL ext4 上 zip（稳定）
cd ~/spc/output && zip -r ~/spc/output.zip . -x "*.DS_Store"
# 验证 zip 完整
unzip -t ~/spc/output.zip | tail -3
# 然后再用方法 1 把单 zip 拷到 Windows
```

### 5. WSL 输出 + 目标盘验证

拷完**必须**验证 size（`Get-Item $dst.Length` 对比源）。不要相信 "cp 没报错 = 成功"。

```powershell
$srcSize = (Get-Item $src).Length
$dstSize = (Get-Item $dst).Length
if ($srcSize -ne $dstSize) {
    Write-Error "size mismatch src=$srcSize dst=$dstSize"
    exit 1
}
```

## 不推荐

- **`cp` 大文件到 `/mnt/c/` 等** — 失败率高，写入不可靠
- **`rsync`** — 没说装（用户 WSL 是 Arch，`pacman -S rsync` 可装但解决不了 9P 写入问题）
- **`mv` 而不是 `cp`** — 跨盘 mv 实际还是 cp + unlink，同样不稳

## 给未来 agent 的提示

如果用户报"WSL 里 cp 到 /mnt/... 没成功"或"文件拷过去 size 是 0 / 不存在"：

1. **不要重试 cp / rsync**——再试几次也是同样结果
2. **直接 PowerShell SMB 路径** + `Copy-Item` 拷文件
3. **必查 distro 名字**（`wsl.exe -l -v`），别用用户口语化的"Ubuntu / Arch"
4. **拷完用 size 验证**（`Get-Item`），不靠 "exit 0 = 成功"
