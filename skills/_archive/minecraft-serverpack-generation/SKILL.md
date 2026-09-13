---
name: minecraft-serverpack-generation
description: "Convert a client Minecraft modpack (CurseForge / Modrinth / Modrinth .mrpack) into a server pack ready to host with Forge / NeoForge / Fabric / Quilt. Use when the user has a modpack zip or modpack instance and wants to run it as a multiplayer server — covers ServerPackCreator (SPC) CLI on WSL/Linux, the Modrinth-vs-CurseForge format difference, the three conf fields cgen leaves blank, the inclusions format for Modrinth overrides/, and the Windows PowerShell SMB path for moving the zip out of WSL."
category: gaming
tags: [minecraft, modpack, serverpack, serverpackcreator, spc, forge, neoforge, fabric, modrinth, curseforge, wsl]
---

# Minecraft Server Pack Generation

把客户端 modpack 转成可部署的服务端包。**互补**于 `minecraft-modpack-server`（那是 host 已有 server pack 的步骤）。

## 触发条件

- 用户有客户端 modpack（PCL/HMCL/官方启动器/Prism 实例目录，或 modrinth .mrpack / curseforge zip），想开服
- 用户说"做这个整合包的服务端" / "我要跑多人服" / "generate a server pack for X"
- 用户说"用 ServerPackCreator 怎么搞" / "spc 怎么用"
- 用户的 modpack 文件路径类似 `E:\.minecraft\versions\XXX\XXX.zip`（Modrinth）或 `C:\Users\<u>\CurseForge\Instances\XXX\`

## 推荐路径（按"用户多快能拿到结果"排序）

### A. Web 端（最省事，2 分钟出结果）

https://serverpackcreator.de

- 上传 modpack zip → 下服务端 zip
- 不要装 Java、不学 CLI、不开 WSL
- 适合：第一次用、不想折腾、本地环境特殊

### B. WSL 本地 CLI（用户偏好"在 WSL 里搞定"，可重复跑）

参见 `references/spc-cli-wsl.md`，涵盖：
- JDK 21 安装
- jar 拉取（注意 JWT 签名 URL 陷阱 + 浏览器替代）
- modpack zip 解压 → cgen → 改 conf → 跑生成
- 输出到 `~/spc/output/` + zip 到 `~/spc/output_server_pack.zip`
- 跨 NTFS 拷贝到 Windows 用 PowerShell SMB 路径（不要 `cp` 大文件到 `/mnt/e/`，会静默截断）

### C. GUI 模式

启动 jar 弹窗口，点点点。WSL 默认 headless 不开 GUI；要 GUI 走 Windows PowerShell 下 jar 启动。

## 关键概念（讲了少踩坑）

| 概念 | 说明 |
|---|---|
| **整合包格式** | Modrinth（`modrinth.index.json` + `overrides/`）vs CurseForge（`manifest.json` + `overrides/`）。SPC 对 CF 自动识别，Modrinth 必须手动配 `inclusions` |
| **客户端 mod fallback list** | SPC 内置 600+ 项纯客户端 mod 名单（OptiFine/Sodium/JEI/NotEnoughAnimations/...），conf `clientMods = []` 时自动用 fallback |
| **`-cgen` + `-config`** | CLI 模式必须两步走。`-feelinglucky` 在 headless 下是 no-op |
| **三必填字段** | `minecraftVersion` / `modLoader` / `modLoaderVersion` — cgen 模板留空，不填 SPC 报 `No directories or files specified for copying` |
| **`inclusions` 格式** | list of `{source, destination, inclusionFilter?, exclusionFilter?}`，source 是 modpack 内的子目录或文件 |
| **输出的 zip 不含 Forge installer** | `start.sh` 第一次跑会从 Mojang/Forge maven 下 jar，**服务器要外网**。离线服务器要手动下 installer |

## 工作流速记（CLI）

```bash
# 1. 解 modpack zip
mkdir -p ~/spc/work/modpack_src && cd ~/spc/work/modpack_src
unzip -q /path/to/modpack.zip
# 看到 modrinth.index.json 或 manifest.json

# 2. 装 JDK + 拿 SPC jar (略，见 references)

# 3. 生成 conf
java -jar spc.jar -cgen ~/spc/work/modpack_src -config ~/ServerPackCreator/configs/x.conf

# 4. 编辑 conf（最少改这 4 行）
#   minecraftVersion = "1.20.1"
#   modLoader = "Forge"
#   modLoaderVersion = "47.4.13"
#   inclusions = [{source="overrides/config",destination="config"}, ...]

# 5. 跑生成（必须前台，Hermes 后台 >60s 必砍）
timeout 580 java -jar spc.jar -config ~/ServerPackCreator/configs/x.conf \
  --destination ~/spc/output < /dev/null > run.log 2>&1
```

## 给未来 agent 的提示

如果用户说"想给这个 modpack 开服"或问"spc 怎么用"：

1. **先看 modpack 来源**：
   - 已有 server pack zip → 用 `minecraft-modpack-server` skill 跑部署
   - 只有客户端 modpack → 用本 skill + `references/spc-cli-wsl.md`
2. **优先 Web 端**试 → 用户拒绝/要自动化再走 CLI
3. **三必填字段 + inclusions** 是 90% 配置失败的原因
4. **输出到 Windows 不用 cp /mnt/** → PowerShell SMB 路径（见 references/wsl-to-windows-file-copy.md）
5. **用户偏好**：能不装东西就不装东西、报错给根因、不给更多试错步骤。WSL 默认用户保持 root，PO 是开发/安装用户

## 参考文件

- `references/spc-cli-wsl.md` — 完整 CLI 流程（jar 获取、JDK 安装、conf 模板、运行陷阱、跨 NTFS 拷贝）
- `references/spc-inclusions.md` — Modrinth 整合包的 `inclusions` 字段配置模板（按 modpack 子目录逐条列出）

## 错误信息速查

| 错误 | 根因 | 修法 |
|---|---|---|
| `No directories or files specified for copying` | Modrinth 包没配 `inclusions` | 配 `inclusions = [{source="overrides/...",destination="..."}, ...]` |
| `Config check not successful. Check your config for errors.` | 同上，或三必填字段空 | 填 `minecraftVersion` / `modLoader` / `modLoaderVersion` |
| `Could not find zipfile directory` (unzip -t 报 jar 坏) | SPC jar 下载被 WSL + 代理掐断，文件头完整但中央目录缺 | 浏览器下到 C:\Users\<u>\Downloads\ 再 cp 进 WSL |
| `bash: 无法设定终端进程组 (-1): 对设备不适当的 ioctl 操作` 在后台完成通知 | Hermes 后台启动 bash 的固定行为，**不是失败** | 看 exit_code 和实际产物判断 |
| `terminal(background=true)` 起的 java 进程 60-90s 后消失 | Hermes sandbox 上限 | 改前台 `timeout 580 java -jar ... < /dev/null > log 2>&1` |
| `cp` 大文件到 `/mnt/e/` 后目标文件不存在 | WSL2 → NTFS 9P 写入不稳 | PowerShell SMB 路径（`\\wsl.localhost\<distro>\...`）+ `Copy-Item` |
