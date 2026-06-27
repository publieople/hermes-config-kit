---
name: quantitative-trading-cn
description: 国内量化交易系统搭建 — 行情终端 vs 量化系统辨析、券商通道瓶颈、开源框架选型、老式行情软件逆向分析
triggers: [量化交易, 自动交易, A股实盘, 期货量化, 条件买卖, 策略回测, 量化系统开发, 行情软件分析, 倚天财经, 通达信]
category: finance
---

# 国内量化交易系统搭建

## 核心认知

**行情终端 ≠ 量化交易系统。** 用户（或其关系人）手里常见的行情软件（倚天财经 OEM、通达信、同花顺等）只能看盘画 K 线，不能自动下单。量化交易系统的完整链路：

```
行情数据 → 策略引擎 → 自动下单 → 券商API → 真实账户
```

## 关键瓶颈：券商通道

代码不是问题——开源框架已经造好 90% 的轮子。真正卡人的是**实盘交易通道**：

| 方式 | 说明 | 门槛 |
|------|------|------|
| 券商量化接口（CTP/XTP） | 正规途径，vnpy 直接对接 | 个人户难开，需机构户或资金门槛 |
| 模拟鼠标操作券商客户端（easytrader） | 野路子，模拟点击同花顺等 | 不稳定，客户端更新就废 |
| 券商自带量化平台（QMT/PTrade/miniQMT） | 部分券商免费提供 | 最省事，但策略受限于平台 |

## 决策框架

动手前必须先确认（不要跳过就开工）：
1. 在哪个券商开户？（决定可用接口）
2. 交易什么品种？（A 股 / 期货 / 可转债 / ETF？）
3. 策略复杂度？（均线交叉级别 vs 多因子 + ML）

如果只是「均线上穿买入、下穿卖出」级别，券商自带的 QMT/miniQMT 免费就能跑，不需要写一行代码。先建议用户确认以上三点再出具体方案。

## 方案速查

| 框架 | 语言 | 场景 | GitHub |
|------|------|------|--------|
| vnpy | Python | 国内期货/股票实盘量化，对接 CTP/XTP | github.com/vnpy/vnpy ⭐29k+ |
| backtrader | Python | 策略回测，文档完善，社区大 | github.com/mementum/backtrader |
| Hikyuu | C++/Python | A 股策略研究 + 回测，高性能 | hikyuu.org |
| QUANTAXIS | Python | 全栈量化（数据+回测+实盘+可视化） | github.com/QUANTAXIS/QUANTAXIS |
| easytrader | Python | 模拟操作券商客户端自动下单 | github.com/shidenggui/easytrader |

数据源：akshare（免费全）、tushare（部分付费）

## 参考

- `references/baiyuncha-analysis.md` — 白云茶行情分析系统完整逆向分析记录（倚天财经 OEM）

## 老式行情软件分析

倚天财经 OEM（如「白云茶行情分析系统」）特征：
- Windows i386 PE32，C++/Delphi 年代产物（约 2000s）
- 架构：exe 主程序 + DLL 组件（SkyCHT.dll 中文/SkyEng.dll 英文） + INI 配置 + 二进制数据文件（.FIN/.FUT/.STK）
- TCP/IP 连接行情服务器接收实时数据
- 功能：实时行情、K 线图、技术指标叠加、画线工具、自选股管理
- **不能交易**，只负责行情展示和人工看图决策

### 分析这类安装包的方法

1. `7z x file.rar` → 解压 RAR
2. `7z x installer.exe` → 二次解压 NSIS 安装包
3. `file *` → 查看文件类型（PE32/DLL/data）
4. `strings *.dll` → 查看 DLL 导出符号
5. `iconv -f gbk -t utf-8 *.ini` → 处理 GBK 编码中文配置
6. 从 IP 地址和 INI 配置推断服务端架构
