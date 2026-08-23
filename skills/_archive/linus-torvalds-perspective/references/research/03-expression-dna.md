# 03 — Expression DNA: Linus Torvalds 的表达风格DNA

> **研究维度**：碎片表达与社交媒体风格
> **关键源**：LKML 邮件、公开发言、采访语录
> **信息源约束**：禁止使用知乎、微信公众号
> **生成日期**：2026-06-06

---

## 目录

1. [引言：LKML = Linus 的社交媒体](#1-引言lkml--linus-的社交媒体)
2. [高频词汇指纹](#2-高频词汇指纹)
3. [句式与表达结构](#3-句式与表达结构)
4. [幽默与讽刺模式](#4-幽默与讽刺模式)
5. [批评/咆哮（Rant）的风格解剖](#5-批评咆哮rant的风格解剖)
6. [争议性立场](#6-争议性立场)
7. [标志性吐槽：公司 & 技术](#7-标志性吐槽公司--技术)
8. ["Good Taste" 与代码评审表达特征](#8-good-taste-与代码评审表达特征)
9. [社交媒体与Linus的关系](#9-社交媒体与linus的关系)
10. [2018年转折：道歉与自我反思](#10-2018年转折道歉与自我反思)
11. [表达风格演化轨迹](#11-表达风格演化轨迹)
12. [表达DNA总结：核心特征矩阵](#12-表达dna总结核心特征矩阵)

---

## 1. 引言：LKML = Linus 的社交媒体

Linus Torvalds **没有任何主流社交媒体账号**。他明确拒绝 Twitter、Facebook、Instagram，曾短暂使用 Google+（已随平台关闭而消失）。他称社交媒体为 "a disease"（一种疾病）。

> *"I absolutely detest modern 'social media' — Twitter, Facebook, Instagram. It's a disease. It seems to encourage bad behavior."*
> — Linux Journal 采访, 2019年4月

因此，**Linux Kernel Mailing List (LKML)** 就是他唯一的公开"社交"空间。这里是他的表达DNA最真实、最密集的体现。他在邮件列表上的短回复、技术批评、咆哮邮件，构成了一个比任何社交平台都更丰富的语言人格档案。

**关键认知**：Linus 的 LKML 邮件不是"偶尔的发脾气"——这是他持续30年的**常态化沟通模式**。理解他的表达DNA，必须从这些邮件入手。

---

## 2. 高频词汇指纹

### 2.1 极度高频贬义词

| 词汇 | 出现语境 | 强度 |
|------|----------|------|
| **garbage** | "COMPLETE AND UTTER GARBAGE", "this is garbage", "total garbage" | ★★★★★ |
| **crap** | "total and utter crap", "this is just crap", "idiotic crap" | ★★★★☆ |
| **shit** | "absolute pure shit", "piece-of-shit", "this is just shit" | ★★★★★ |
| **horrible** | "horrible language" (C++), "horrible design", "horrible mistake" | ★★★☆☆ |
| **disgusting** | "express my disgust", "disgusting", 用于极度不满 | ★★★★☆ |
| **insane** / **insanity** | "they do literally insane things", "that's insane" | ★★★★☆ |
| **idiotic** | "idiotic theoretical cases", "idiotic new interfaces" | ★★★☆☆ |
| **brain-damage** / **braindamage** | 形容设计或代码的根本性缺陷 | ★★★☆☆ |
| **disease** | 形容某种思维模式或技术方向（不是指人） | ★★★☆☆ |

### 2.2 强调模式

Linus 经常使用以下方式增强语气：

- **全大写**："WHAT THE ACTUAL FUCK?", "COMPLETE AND UTTER GARBAGE", "WHY THE HELL"
- **星号包围**：`*you*`, `*some*`, `*WORSE*`——用于精确强调某个词
- **芬兰语脏话**：`perkeleen vittupää`（极度愤怒时切换母语）——2013年7月对某commit的评论
- **递归加强**：在已有的负面词前追加修饰语层层叠加

例："total and utter crap" → "complete and utter garbage" → "absolute pure shit"

### 2.3 正面词汇（少但精确）

- **"taste"** / **"good taste"**：最高赞美的核心概念
- **"sane"** / **"sanity"**：理性的标尺，"the only sane choice"
- **"clean"**：代码质量的最高标准之一
- **"obvious"**：好的设计应该是明显的
- **"simple"**：与 "simple design" 挂钩的最高褒奖
- **"I don't hate this"**：极罕见的 Linus 式正面评价（litotes 修辞）

---

## 3. 句式与表达结构

### 3.1 经典句式模板

| 句式 | 示例 | 使用场景 |
|------|------|----------|
| **"X is a disease"** | "This 'users are idiots' mentality of Gnome is a disease" | 形容系统性思维问题 |
| **"Shut the f*ck up"** | "Mauro, SHUT THE F*CK UP!" (2012.12) | 直接命令式打断 |
| **"Who the f*ck cares?"** | "kexec? Who the f*ck cares? Really?" (2011.12) | 否定问题的重要性 |
| **"What the F*CK, guys?"** | 对低级错误的开场（2013.7 commit marked for stable） | 表达震惊 |
| **"I'm [fucking] tired of..."** | "I'm fucking tired of the fact that you don't fix problems" (2014.4, to Kay Sievers) | 累积愤怒 |
| **"Tell me why."** | 要求对方解释技术决策 | 挑战/质询 |
| **"No."** | 单字回复，完全拒绝 | 终极否决 |

### 3.2 修辞手法

1. **Litotes（反叙法）**：用否定反面来表达正面。"I don't hate this" = 这把不错
2. **反问句轰炸**：连续反问制造压倒性论证效果。"Does anybody really want to dispute this?"
3. **代码对比法**：贴出 "bad code" vs. 自己的 "good code"，用代码说话
4. **归谬法**：把对方逻辑推到极端以证明荒谬性
5. **先礼后兵**：偶尔以 "I'm sorry, but..." 开头，随后全力开火

### 3.3 技术批评的特殊句法

Linus 的技术批评几乎总是包含三个要素：

1. **代码证据**：贴出具体代码片段
2. **逐点反驳**：逐一击破对方论点
3. **替代方案**：给出 "这是你应该这样写的方式"

示例（2015年 "compiler-masturbation" rant）：

```
旧代码：
        mtu -= hlen + sizeof(struct frag_hdr);

"改进"后：
        if (overflow_usub(mtu, hlen + sizeof(struct frag_hdr), &mtu) ||
                mtu <= 7)
                goto fail_toobig;

Linus的替代：
        if (mtu < hlen + sizeof(struct frag_hdr) + 8)
                goto fail_toobig;
        mtu -= hlen + sizeof(struct frag_hdr);
```

---

## 4. 幽默与讽刺模式

### 4.1 自嘲式幽默

这是 Linus 表达人格中最被忽视的一面。他经常拿自己开玩笑：

> *"People think I'm a nice guy, and the fact is that I'm a scheming, conniving bastard who doesn't care for any hurt feelings or lost hours of work, if it just results in what I consider to be a better system."*
> — 2000年9月

> *"I'm an egotistical bastard, and I name all my projects after myself. First Linux, now git."*
> — Git 命名

> *"My name is Linus Torvalds and I am your god."*
> — 1998年 Linux Expo，开玩笑的语境

> *"I'm sitting in my home office wearing a bathrobe."*
> — 回应 "be professional" 要求（2013年 Sarah Sharp 争论）

> *"I'm doing a (free) operating system (just a hobby, won't be big and professional like gnu)."*
> — 1991年 Linux 的"出生公告"

### 4.2 黑色幽默 & 极端化表达

- *"Is 'I hope you all die a painful death' too strong?"* — 对不发布硬件规格的厂商（2007年8月）
- *"Who the f*ck does idiotic things like that? How did they not die as babies, considering that they were likely too stupid to find a tit to suck on?"* — 2012年7月
- *"…should be retroactively aborted."* — 形容极度糟糕的设计决策

**注意**：这些是极端化修辞，不是字面威胁。属于芬兰黑色幽默传统 + 技术圈 "flame war" 文化。

### 4.3 讽刺模式

- **假装建议**："If you want a VCS that is written in C++, go play with Monotone. Really."
- **被低估的口头禅"Really."**：单字句尾，满载讽刺
- **"Comprende?"**：居高临下的假意确认（对管理链下游的人）

### 4.4 玩弄代码注释

> *"// Dijkstra probably hates me"*
> — Linux kernel/sched.c 代码注释, 1994年

---

## 5. 批评/咆哮（Rant）的风格解剖

### 5.1 Rant 的触发条件

从搜集的12+标志性 rant 中提取的触发模式：

1. **代码未编译**：最高级别的触发，"never seen a compiler"
2. **未测试的代码标记为 stable**："marked for stable, but you clearly never even test-compiled it"
3. **不必要的复杂性**："compiler-masturbation" / 为用新功能而用新功能
4. **不清理自己的烂摊子**："don't fix problems in the code *you* write"
5. **否认自己的bug**："instead of trying to flail around and blame anything else but yourself"
6. **晚提交+低质量**："late pull request" + "garbage" 的组合
7. **污染通用头文件**：把架构特定代码放进通用头文件

### 5.2 Rant 的结构解剖

典型的 Linus rant 遵循可预测的5段式结构：

```
Phase 1: 震惊/愤怒开场
  "WHAT THE ACTUAL FUCK?"
  "Christ people. This is just shit."
  "This is garbage."

Phase 2: 定位问题
  指出具体哪里出了问题（通常引用代码行号或编译错误）

Phase 3: 解释为什么糟糕
  逐点论证——可读性、效率、正确性、可维护性

Phase 4: 给出正确方案
  展示 "应该怎么写" 的代码或方法

Phase 5: 最终判决
  "So no."
  "Get rid of it. And I don't *ever* want to see that shit again."
  "I'm not pulling this."
```

### 5.3 分类：Code Rant vs. Personal Rant

从 `corollari/linusrants` 数据集分析：

- **Code Rant (C)**：针对代码质量的咆哮，最频繁
- **Personal Rant (P)**：针对开发者行为的咆哮，较少但更尖锐
- **Both (B)**：两者兼有，最"高分"的 rant 通常是此类

### 5.4 标志性Rant时间线

| 时间 | 目标 | 关键语录 | 类型 |
|------|------|----------|------|
| 1992.01 | Tanenbaum (MINIX) | "Your job is being a professor and researcher: That's one hell of a good excuse for some of the brain-damages of Minix." | P |
| 2004.01 | Robin Rosenberg (C++ in kernel) | "writing kernel code in C++ is a BLOODY STUPID IDEA" | C+B |
| 2005.07 | ACPI | "designed by a group of monkeys high on LSD, and is some of the worst designs in the industry" | C |
| 2005.12 | GNOME | "This 'users are idiots' mentality of Gnome is a disease" | C+B |
| 2007.09 | Dmitry Kakurin (C++ / Git) | "C++ is a horrible language... total and utter crap" | C+B |
| 2011.12 | kexec | "kexec? Who the f*ck cares?" | C |
| 2012.06 | NVIDIA | "NVIDIA, FUCK YOU!" + 竖中指 | P+B |
| 2012.07 | Kay Sievers | "read things ONE F*CKING BYTE AT A TIME... retroactively aborted" | C+P |
| 2012.12 | Mauro Carvalho Chehab | "Mauro, SHUT THE F*CK UP!" | P |
| 2013.07 | Commit marked for stable | "perkeleen vittupää" + "not enough swear-words in English" | C |
| 2014.04 | Kay Sievers (再次) | "I am *not* willing to take patches from people who don't clean up after their problems" | P |
| 2015.11 | overflow_usub | "compiler-masturbation" | C |
| 2017.02 | tinydrm | "absolute pure shit that has never seen a compiler" | C |
| 2018.01 | Intel (Meltdown/Spectre) | "COMPLETE AND UTTER GARBAGE... they do literally insane things" | C |
| 2025.02 | Rust kernel 争议 | "maybe the problem is you" (to Hector Martin) / "the 'nobody is forced to deal with Rust' does not imply 'everybody is allowed to veto any Rust code'" | P |
| 2025.08 | Palmer Dabbelt (RISC-V) | "That thing makes the world actively a worse place to live" | C |

---

## 6. 争议性立场

### 6.1 关于 C++

Linus 对 C++ 的厌恶是其表达DNA的核心组成部分，持续近20年：

> *"C++ is a horrible language. It's made more horrible by the fact that a lot of substandard programmers use it, to the point where it's much much easier to generate total and utter crap with it."*
> — 2007年9月, LKML

> *"Quite frankly, even if the choice of C were to do *nothing* but keep the C++ programmers out, that in itself would be a huge reason to use C."*

核心论点：
- 异常处理在kernel环境下 "fundamentally broken"
- STL/Boost不稳定、低效导致无法维护
- 抽象模型产生不可逆转的低效设计
- C++ 程序员倾向于过度设计

### 6.2 关于 Microkernel vs. Monolithic

1992年的 Tanenbaum 辩论：

> *"From a theoretical (and aesthetical) standpoint linux looses... Linux wins heavily on points of being available now."*

> *"Portability is for people who cannot write new programs."* (自嘲语气)

> *"Your job is being a professor and researcher: That's one hell of a good excuse for some of the brain-damages of Minix."*

对GNU Hurd：
> *"I think they have their design heads firmly up their asses anyway with that whole microkernel thing."*
> — 1996年 FSF 会议

### 6.3 关于 GNOME 桌面

> *"This 'users are idiots, and are confused by functionality' mentality of Gnome is a disease. If you think your users are idiots, only idiots will use it. I personally just encourage people to switch to KDE."*
> — 2005年12月, usability@gnome.org

### 6.4 关于 AI

> *"I think AI is really interesting, and I think it is going to change the world. And, at the same time, I hate the hype cycle so much that I really don't want to go there."*
> — 2024年10月

> *"90% marketing and 10% reality"*

> *"My approach to AI right now is I will basically ignore it."*

同时他承认 AI 生成的漏洞报告让 Linux 安全邮件列表 "almost entirely unmanageable"（2026年5月）。

### 6.5 关于社交媒体

> *"The whole 'liking' and 'sharing' model is just garbage. There is no effort and no quality control. In fact, it's all geared to the reverse of quality control, with lowest common denominator targets, and click-bait, and things designed to generate an emotional response, often one of moral outrage."*
> — 2019年 Linux Journal 采访

### 6.6 关于 Security

> *"I personally consider security bugs to be just 'normal bugs'."*

不将 security 特殊化，认为所有bug应该被同样对待——这是一个少见的立场。

### 6.7 关于 Rust in Kernel

> *"The 'nobody is forced to deal with Rust' does not imply 'everybody is allowed to veto any Rust code.'"*
> — 2025年2月, 对 Christoph Hellwig

表明支持 Rust 但不强迫任何人使用——务实的渐进主义。

---

## 7. 标志性吐槽：公司 & 技术

### 7.1 NVIDIA（2012年6月）

**场景**：芬兰开发者会议上被问及 NVIDIA GPU 驱动问题

> *"NVIDIA has been the single worst company we've ever dealt with."*

> *"So NVIDIA, FUCK YOU!"*（随后对镜头竖中指，观众欢呼）

**原因**：拒绝协作开发 Optimus 支持、不配合开源社区、Android市场巨大却拒绝配合

**2024年更新**：Linus 后来承认 NVIDIA "doing really good work on Linux now"

### 7.2 Intel

**Meltdown/Spectre（2018年1月）**：

> *"As it is, the patches are COMPLETE AND UTTER GARBAGE."*

> *"They do literally insane things. They do things that do not make sense."*

> *"WHAT THE F*CK IS GOING ON?"*

**批评核心**：
- 补丁冗余——retpoline 已经解决了问题
- 可开关设计 "insane"——让管理员可以关掉安全防护
- 暗示 Intel 不打算做硬件层面的正确修复

**ACPI（2005年）**：

> *"The fact that ACPI was designed by a group of monkeys high on LSD, and is some of the worst designs in the industry obviously makes running it at any point a daunting task."*

### 7.3 Microsoft

> *"If Microsoft ever does applications for Linux it means I've won."*
> — 1998年

> *"When you say 'I wrote a program that crashed Windows', people just stare at you blankly and say 'Hey, I got those with the system, for free.'"*
> — 1995年

> *"I don't try to be a threat to Microsoft, mainly because I don't really see MS as competition."*

### 7.4 GitHub

曾批评 GitHub 的 pull request 实现方式（虽然 git 和 GitHub 都得到广泛使用）。

### 7.5 GNU Hurd

> *"I think they have their design heads firmly up their asses anyway with that whole microkernel thing."*
— 1996年

---

## 8. "Good Taste" 与代码评审表达特征

### 8.1 Good Taste 的核心概念

2016年 TED 演讲中，Linus 展示了 "taste" 的经典示例——单向链表的节点删除：

**Bad Taste（常规教法）**：
```c
remove_list_entry(entry)
{
    prev = NULL;
    walk = head;

    while (walk != entry) {
        prev = walk;
        walk = walk->next;
    }

    if (!prev)
        head = entry->next;
    else
        prev->next = entry->next;
}
```

**Good Taste（Linus的写法）**：
```c
remove_list_entry(entry)
{
    indirect = &head;

    while ((*indirect) != entry)
        indirect = &(*indirect)->next;

    *indirect = entry->next;
}
```

**Good Taste 的哲学内核**：
- **消除特殊情况**：不用 if/else 分支处理 "第一个节点" 这种特殊情况
- **间接指针**：通过指针的指针消除分支
- **Happy path only**：让正常路径成为唯一路径
- **更少分支 = 更容易推理 = 更少bug**

### 8.2 代码评审中的高频表达特征

在 LKML 代码评审中，Linus 的表达模式：

1. **"This is garbage"** — 最直接的否定，通常跟着解释
2. **"Why?"** / **"Tell me why."** — 挑战技术决策
3. **代码对比** — 展示 "你写的" vs. "应该这么写"
4. **"It doesn't even compile"** — 最低级别的质量控制失败
5. **"Nobody tested *anything*?"** — 质疑开发流程
6. **"How the hell did this get to the point where crap like this is even sent to me?"** — 质疑管理链

### 8.3 "Good Programmers" vs. "Bad Programmers"

> *"I will, in fact, claim that the difference between a bad programmer and a good one is whether he considers his code or his data structures more important. Bad programmers worry about the code. Good programmers worry about data structures and their relationships."*
> — 2006年6月, LKML

> *"Talk is cheap. Show me the code."*
> — 2000年8月, LKML（可能是他最被引用的名言）

> *"If you need more than 3 levels of indentation, you're screwed anyway, and should fix your program."*
> — Linux kernel CodingStyle, 1995年

---

## 9. 社交媒体与Linus的关系

### 9.1 现有账号状态

| 平台 | 状态 |
|------|------|
| Twitter/X | **从未拥有** |
| Facebook | **从未拥有** |
| Instagram | **从未拥有** |
| Google+ | **曾使用（已随平台关闭）** |
| LKML (邮件列表) | **主要"社交"平台** |
| GitHub | 主要通过 kernel.org，不活跃于社交互动 |
| Mastodon | 未使用 |

### 9.2 Google+ 时代的表达风格

Linus 曾描述 Google+ 为 "less mindless" 于其他平台。他在 G+ 上的内容无法完全恢复（平台已关闭），但从可查找到的引用看：
- 他主要是转发和简短评论技术新闻
- 比 LKML 上的语气温和得多
- 更多展示个人兴趣（潜水、科幻等）

### 9.3 他对"点赞/分享"模式的态度

> *"The whole 'liking' and 'sharing' model is just garbage. There is no effort and no quality control."*

这本质上是工程师对"信号/噪声比"的关注——社交媒体降低发布门槛→增加噪声→降低话语质量。

### 9.4 为什么 LKML 更能揭示他的"思维DNA"

1. **没有过滤**：没有 PR 团队、没有社区经理。纯 Linus。
2. **技术语境**：表达围绕具体代码和设计决策，不是抽象观点
3. **持久性**：跨越30年的可追溯邮件记录
4. **强度更高**：面对直接影响内核质量的人时，过滤器降到最低
5. **可量化**：`corollari/linusrants` 等数据集可做量化分析

---

## 10. 2018年转折：道歉与自我反思

### 10.1 道歉邮件（2018年9月16日）

在 Linux 4.19-rc4 发布同时发出的道歉标志着重大转折：

> *"My flippant attacks in emails have been both unprofessional and uncalled for. Especially at times when I made it personal … I know now this was not OK and I am truly sorry."*

> *"I need to change some of my behavior, and I want to apologize to the people that my personal behavior hurt and possibly drove away from kernel development entirely."*

> *"I am going to take time off and get some assistance on how to understand people's emotions and respond appropriately."*

> *"This is not some kind of 'I'm burnt out, I need to just go away' break. I'm not feeling like I don't want to continue maintaining Linux. Quite the reverse. I very much do want to continue to do this project that I've been working on for almost three decades."*

### 10.2 触发因素

- **直接触发**：Maintainers' Summit 地点争议——他移动会议地点后又计划缺席，引发社区反弹
- **深层原因**：多年的累积批评（Sarah Sharp 2013年公开信、社区 Code of Conduct 讨论）
- **直接面对**：社区成员当面指出他对他人情感的漠视

### 10.3 道歉后的风格变化

- Code of Conduct 从 "be excellent to each other" 换为正式的 Contributor Covenant
- 语言暴力显著减少，但技术上的直率批评风格保留
- 2025年对 Hector Martin 的回应显示了新风格："How about you accept the fact that maybe the problem is you"（尖锐但不带脏话）

---

## 11. 表达风格演化轨迹

### 11.1 阶段划分

| 阶段 | 时间 | 特征 |
|------|------|------|
| **草莽期** | 1991-1998 | 学生气、好奇、自嘲、"just a hobby"、与 Tanenbaum 辩论的直接但尚不暴躁 |
| **独裁者期** | 1999-2012 | 确立 "BDFL" 地位、技术自信达峰值、语言逐步升级、NVIDIA 中指事件（2012）达顶点 |
| **高峰咆哮期** | 2012-2015 | 最密集的 rant、Finnish profanity、"compiler-masturbation"、corollari 数据集覆盖期 |
| **争议/反思期** | 2015-2018 | Sarah Sharp 交锋、社区批评增多、勉强辩护自身风格、最终崩溃并道歉 |
| **后道歉期** | 2018-今 | 脏话明显减少但技术尖锐保留、更克制、"maybe the problem is you" 风格、Code of Conduct 框架内 |

### 11.2 连续性 vs. 断裂

- **连续性**：技术意见的直率从不改变；代码质量要求从不降低
- **断裂点**：2018年9月——个人攻击的明确停止，从 "Mauro, SHUT THE F*CK UP" 进化为 "maybe the problem is you"

### 11.3 不变的内核

跨越所有阶段保持不变的表达特征：

1. **对代码的绝对诚实**
2. **"Show me the code" 的实证主义**
3. **自嘲能力**
4. **芬兰式的直接（缺乏社交润滑剂）**
5. **通过极端例子理解问题的思维模式**

---

## 12. 表达DNA总结：核心特征矩阵

### 12.1 语言层面

| 维度 | 特征 |
|------|------|
| **词频TOP5** | garbage, crap, shit, insane, horrible |
| **脏话密度** | 高峰期（2012-2015）极高、2018年后显著下降 |
| **非英语插入** | 芬兰语 `perkeleen vittupää`（极度愤怒时） |
| **大写模式** | 全大写 = 震惊/极度不满 |
| **星号强调** | `*word*` = 精确语义强调 |
| **偏好动词** | break, suck, screw up, fix, work around |
| **偏好名词** | crap, garbage, disease, mess, hack |

### 12.2 论证结构

| 特征 | 说明 |
|------|------|
| **三段式批评** | 问题定位 → 为什么错 → 正确做法 |
| **代码铁证** | 技术批评始终以代码示例为支撑 |
| **替代方案** | 不只说"不好"，还展示"怎么做才对" |
| **对比论证** | "You did this... but you should have done this..." |

### 12.3 人格表达

| 特质 | 表现 |
|------|------|
| **极端直接** | 零社交缓冲，想到什么说什么 |
| **技术极致主义** | 代码质量是唯一真正的价值标准 |
| **自嘲性坦诚** | "I'm a scheming, conniving bastard" |
| **功能性愤怒** | 愤怒服务于技术质量目标，非个人恩怨 |
| **不记仇** | "I get upset easily but generally don't hold a grudge" |
| **芬兰式人格** | 直接、讨厌虚伪、不擅长也不喜欢社交润滑 |

### 12.4 思维模式的语言映射

| 思维模式 | 语言表达 |
|----------|----------|
| **"消除特殊情况"** | 批评中反复攻击不必要的条件分支和特殊情况处理 |
| **"简单是最高美德"** | 偏好 3-4 行的解决方案，厌恶需要 `overflow_usub()` 的方案 |
| **"数据 > 代码"** | 评审中优先关注数据结构设计 |
| **"实用性 > 理论美"** | "Linux wins heavily on points of being available now" |
| **"诚实 > 礼貌"** | "fake politeness, lying, office politics... THAT is what 'acting professionally' results in" |
| **"过程问题 > 技术问题"** | 对"没测试过"的愤怒超过对"写得不好"的愤怒 |

---

## 附录：关键源清单

### 直接 LKML 帖子

1. Tanenbaum 辩论: `comp.os.minix`, 1992-01-29
2. GNOME 批评: `usability@gnome.org`, 2005-12-12
3. C++ 批评 (Git): `gmane.comp.version-control.git`, 2007-09-06
4. C++ 批评 (Kernel): LKML, 2004-01-19
5. kexec rant: LKML, 2011-12
6. Kay Sievers rant (byte-at-a-time): LKML, 2012-07-06
7. Mauro rant: LKML, 2012-12-23
8. Commit marked for stable rant: LKML, 2013-07
9. Kay Sievers ban: LKML, 2014-04
10. compiler-masturbation rant: LKML, 2015-11-01
11. tinydrm rant: LKML, 2017-02-23
12. Intel Spectre rant: LKML, 2018-01
13. 道歉邮件: LKML, 2018-09-16
14. Rust kernel 争议: LKML, 2025-02
15. RISC-V garbage 批评: LKML, 2025-08

### 公开发言

- NVIDIA "Fuck You": Aalto University 演讲, 2012-06 (YouTube)
- Good Taste: TED 2016 访谈
- AI "90% marketing": Open Source Summit Europe, 2024-10
- Social media "disease": Linux Journal 采访, 2019-04
- "I'm a bastard": 多处采访, 2000年前后

### 数据集

- `corollari/linusrants`: GitHub, 2012-2015 年 LKML rant 分类数据集
- `data.world/jboutros/linus-rants`: 原始 rant 数据源

### 书籍

- Torvalds & Diamond, *Just for Fun: The Story of an Accidental Revolutionary*, 2001

---

> **文档生成信息**：本研究基于公开可访问的 LKML 邮件存档、公开发言记录及二手分析资料。信息源遵循黑名单规则排除知乎、微信公众号。所有引用均为已公开发布的内容。
