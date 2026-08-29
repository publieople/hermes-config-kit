# 白云茶行情分析系统 分析记录

> 2025-06-23 分析，来源：用户他爸提供的 `.rar` 安装包

## 基本信息

- **文件**：白云茶、老树红茶，沁园红茶，倚天行情端(9).rar (3.7MB)
- **性质**：倚天财经（ytcj.com）OEM 贴牌行情终端
- **技术栈**：Windows i386 PE32，Nullsoft Installer (NSIS-3) 打包
- **年代**：约 2000s，32 位 C++/Delphi 产物

## 解压后文件结构

```
bycyt.exe (3.7MB, NSIS installer)
├── isky.exe — 主程序（倚天财经行情端核心）
├── SkyCHT.dll — 中文语言/功能组件
├── SkyEng.dll — 英文语言/功能组件
├── C4dll.dll — 行情数据组件
├── vic32.dll — 老旧 Windows GUI 组件
├── ZipArchive.dll — 压缩包支持
├── skyUpdate2.exe — 在线更新程序
├── Uninstall.exe — 卸载程序
├── ICONFIG.ini — 主配置
│   ├── TEST_USER=gzcy
│   ├── SPECIAL=MMV;YTTL;BSSM;BSCG;BSSMD
│   └── UPDATE=http://ytcj.com/download/winupdate.exe
├── ip.txt — 服务器地址: 47.111.120.131（白云茶行情服务器）
├── license.txt — "倚天财经荣誉出品 授权白云茶分析系统及其客户使用"
├── URL.txt — 空
├── tod.txt — 操作说明（GBK 编码中文）
├── sky2000.ico/jpg — 图标/背景
├── SYS/
│   ├── BASE.FIN — 基础数据（二进制）
│   ├── CONDITION.FUT — 期货条件（二进制）
│   ├── CONDITION.STK — 股票条件（二进制）
│   ├── luna.dat — 主题数据
│   └── tod.txt — 使用提示
└── USERS/
    ├── C.ini — C/C++ 语法高亮配置
    ├── C2.ini — 第二语言高亮
    ├── C3.ini — 第三语言高亮
    └── alert.WAV — 告警音效
```

## 功能推断

从 tod.txt 操作说明和 INI 配置推断：
- 实时行情接收（TCP 连 47.111.120.131）
- K 线图表展示（日线/分钟线）
- 技术指标叠加（均线、MACD、RSI 等）
- 画线工具（趋势线、通道等）
- 多窗口/多图组合
- 自选股管理
- F1-F12 快捷键操作
- 右键菜单功能
- **无交易下单功能**

## 服务端

- IP: 47.111.120.131
- 域名: ytcj.com（倚天财经官网）
- 测试账户: gzcy

## 分析方法

```bash
# 解压 RAR
7z x "file.rar" -y

# 解压 NSIS 安装包
7z x bycyt.exe -y

# 识别文件类型
file *.dll *.exe

# 读取 GBK 编码中文文件
iconv -f gbk -t utf-8 license.txt
iconv -f gbk -t utf-8 ICONFIG.ini
iconv -f gbk -t utf-8 SYS/tod.txt

# 查看 DLL 字符串
strings SkyCHT.dll | head -30
```
