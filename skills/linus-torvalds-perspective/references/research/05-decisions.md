# Linus Torvalds 重大决策与行动记录

> **Agent 5 — 决策记录/行动维度**  
> **生成日期**: 2026-06-06  
> **可信度评级**: High（Linus本人邮件/帖文/采访原文）> Medium-High（专业媒体报道）> Medium（第三方分析/社群讨论）

---

## 一、创建Linux的决策（1991年）

### 决策背景

- **时间线**: 1991年1月5日购入Intel 80386 PC，同年4月开始写代码，7月3日首次在comp.os.minix发帖询问POSIX标准
- **个人状态**: 芬兰赫尔辛基大学21岁学生，经济拮据
- **直接动机**:
  - Minix用户但不满足——Minix是教学用微内核系统，功能受限
  - 想深入理解386硬件——"It was also a project to teach me about the 386"
  - 需要更好的终端模拟器来拨号访问大学计算机读邮件和新闻
  - $169的Minix价格让穷学生不悦，想做真正免费的替代品

### 决策过程

Linus的经典Usenet帖子（1991年8月25日）：

> "I'm doing a (free) operating system (just a hobby, won't be big and professional like gnu) for 386(486) AT clones. This has been brewing since april, and is starting to get ready."

关键事实：
- 当时已知bash(1.08)和gcc(1.40)已能在其上运行
- "It is NOT portable (uses 386 task switching etc), and it probably never will support anything other than AT-harddisks"
- 完全不含Minix代码，"free of any minix code"

### 事后反思

- Linus在1992年回顾中说："The project was obviously linux, so by July 3rd I had started to think about actual user-level things"
- 最著名的预测失误："won't be big and professional like gnu"——今天Linux运行在96%以上的一百万顶级Web服务器、全部500台最快超级计算机上
- Linus从未预言Linux的成功；他在后来的采访中反复强调这只是个人项目，从未有宏伟蓝图

### 言行一致性分析

- **一致**: "just a hobby"的谦逊态度始终保持，Linus至今否认自己是visionary
- **不一致**: 预测"won't be big"与后来积极维护和扩展形成对比——但他将这种演变归因于"社区贡献"而非个人规划

**来源**:
- Linus Torvalds原始Usenet帖子, comp.os.minix, 1991年8月25日 [Google Groups Archive - 可信度: High]
- "LINUX's History by Linus Torvalds" (1992年7月31日自述), CMU CS Archive, https://www.cs.cmu.edu/~awb/linux.history.html [可信度: High]
- "History of Linux", Wikipedia [可信度: Medium-High]

---

## 二、GPLv2授权决策（1991年末-1992年初）

### 最初许可证

Linus自己写的简单许可证，核心两条：
1. **完整源码必须可用** ("full source has to be available")
2. **不得涉及金钱** ("no money may be involved")

> "The 'no money' part came about because I had been annoyed with (being a rather poor student) having to pay something like $169 USD for Minix" — Linus Torvalds

Linus明确指出，对他来说 **"free as in gratis"（免费如啤酒）** 比 "free as in freedom"（自由如言论）更早成为关注点。

### 切换到GPLv2的决策逻辑

关键转折：有人想在本地Unix用户组会议上分发Linux拷贝，希望至少收回复制成本。

Linus的推理链：
1. 收回复制成本是合理的
2. 一旦允许收成本费，就没有明确界限了——所以"禁止金钱"这个条款本身失去了意义
3. 只要源码仍然可在互联网上免费获取，金钱方面就不成问题
4. 有人建议他用GPLv2，他决定不自己重写许可证，直接采用现有成熟许可证
5. 选用GPLv2也是对gcc的致敬——gcc对Linux项目至关重要

> "I felt that as long as people gave access to source back, I could always make it available on the internet for free, so the money angle really had been misplaced in the copyright." — Linus Torvalds

### GPLv2 ONLY 而非 "GPLv2 or later" 的决策

Linux内核采用 **GPLv2 only**（不含"or any later version"条款），这是一个重大且持续影响至今的决策。这意味着迁移到GPLv3需要所有贡献者同意。

### 拒绝GPLv3的立场（2007年至今）

当FSF发布GPLv3时，Linus明确拒绝将内核迁移到GPLv3。核心理由：

1. **反DRM条款越界**：GPLv3的anti-Tivoization条款试图通过软件许可证控制硬件行为
   > "I literally feel that we do not — as software developers — have the moral right to enforce our rules on hardware manufacturers."
   
2. **数字签名和安全性**：GPLv3要求分发私钥以便用户签名修改后的内核，Linus认为这是"INSANE"——破坏了安全启动、模块签名等合理安全机制

3. **实用主义 vs 理想主义**：Linus的核心哲学——GPL的目的是确保代码改进回馈社区（quid pro quo），而非推进政治议程
   > "The GPL already requires source code. So the GPL already does have an anti-DRM clause as far as the software is concerned."
   
4. **对FSF的态度**：2007年Linus写道"I'm damn fed up with the FSF"，认为GPLv3"violates everything that GPLv2 stood for"

### 事后反思

- Linus明确表示他不反对GPLv3本身——"I'm not arguing against the GPLv3. I'm arguing that the GPLv3 is wrong for me"
- 允许商业使用被证明是非常正确的——"clearly allowing the commercial side has been a very good thing for everybody"
- Linux内核至今仍是GPLv2 only，证明了这一决策的持久性

### 言行一致性分析

- **一致**: 从最初"免费"动机→GPLv2（允许收费但要求开源）→拒绝GPLv3（不强制硬件开放），始终贯彻"我们只控制软件，不控制硬件"的原则
- **一致**: 实用主义贯穿始终——许可证是工程工具而非道德十字军旗帜

**来源**:
- Linus Torvalds采访, Data Center Knowledge (The VAR Guy), 2016年8月23日, https://www.datacenterknowledge.com/business/linus-torvalds-on-early-linux-history-gpl-license-and-money [可信度: High - 直接引用Linus原话]
- "Torvalds versus GPLv3 DRM restrictions", Linux.com (Joe Barr), https://www.linux.com/news/torvalds-versus-gplv3-drm-restrictions [可信度: High - 引用LKML原文]
- "Linus and the GPLv3 - the saga continues", FOSSwire, 2007年7月, https://fosswire.com/post/2007/07/linus-and-the-gplv3-the-saga-continues [可信度: Medium-High]

---

## 三、创建Git的决策（2005年）

### 决策背景

**1991-2002: 无版本控制时代**
- Linux内核开发完全靠邮件列表+手动打补丁
- Linus手动将补丁应用到自己的源码树
- 发布是整个树的完整快照，历史记录只是一个巨大的diff

**2002年: 选择BitKeeper的争议性决策**
- 内核社区强烈要求引入版本控制。CVS存在但被Linus拒绝（逐文件追踪、竞态条件、无法逻辑分组补丁）
- Subversion尝试修复CVS但依然不满足Linus未明说的需求
- Linus出人意料地选择了 **闭源的商业系统BitKeeper**——引起了自由软件社区的强烈不满

> "He was not a free software zealot. He would use open-source tools if they were better than their commercial counterparts. But if a commercial tool was better, he wouldn't turn his nose up."

BitKeeper的关键优势：**分布式开发**——整个仓库可被fork和merge，支持"副官模型"（lieutenants model）

### 触发事件：Tridgell事件（2005年4月）

- Andrew Tridgell（Samba/rsync作者）试图逆向工程BitKeeper的网络协议来构建自由替代品
- BitMover（Larry McVoy）此前已警告此举将导致免费许可终止
- **结果**：BitMover撤回了Linux社区的免费使用许可，内核开发一夜之间失去了核心工具链

### 创建Git的核心决策

Linus做出了几个关键选择：

1. **停止所有内核开发**——自1991年以来首次
2. **不采用任何现有工具**——arch、darcs、monotone都试过，均不满足需求
3. **自己写一个**——在两周内完成

### 设计哲学

最核心的要求：**速度**

> "With thousands of kernel developers across the world submitting patches full-tilt, he needed something that could operate at speeds never before imagined. He couldn't afford to wait longer than a few seconds for even the largest and most complex operation to finish."

反直觉的设计选择：
- Git存储 **完整文件版本** 而非补丁（patch）
- 设计更像 **底层文件系统操作** 而非传统VCS
- 最初让社区感到困惑——与任何见过的东西都不同

### 时间线

- 2005年6月：开始编码，数天内Git实现自托管（self-hosting）
- 数周内：可承载Linux内核
- 数月内：功能完整
- Linus随即交出维护权给 **Junio C. Hamano**，回归内核开发

### Git vs Subversion的技术争论

Linus对Subversion的评价——"the most pointless project ever started"——源自他对集中式版本控制的根本性反对。他认为分布式是唯一正确方案，这在20年后已被完全验证。

### 事后反思

- Linus在2022年Open Source Summit上说："I only worked on Git for six months"——将全部功劳归于Junio Hamano
- "My daughter went to college for computer science...she told me that in her CS department, I am solely credited with the creation of Git"
- Linus至今认为Git的成功在于它解决了正确的问题（内容追踪），而非它试图成为"版本控制系统"

### 言行一致性分析

- **一致性核心案例**: Linus不会为意识形态牺牲工程质量——先用闭源BitKeeper，后用自家Git，标准始终是"什么工具最好用"
- **一致**: 用完就放手——Git写完就交给Hamano维护，与Linux的"仁慈独裁者"模式一致
- **有趣对比**: 他在2007年明确说选择C而非C++写Git，部分原因是为了排挤C++程序员。Git成功的工程品质验证了这一偏执选择

**来源**:
- "A Git Origin Story", Linux Journal, https://www.linuxjournal.com/content/git-origin-story [可信度: High]
- "Git at 20", Michael Tsai Blog, 2025年4月15日, https://mjtsai.com/blog/2025/04/15/git-at-20 [可信度: High]
- Linus Torvalds采访, The New Stack (Open Source Summit 2022), https://thenewstack.io/rust-in-the-linux-kernel-by-2023-linus-torvalds-predicts [可信度: High]

---

## 四、拒绝Microkernel架构（1992年，Tanenbaum-Torvalds辩论）

### 决策背景

1992年初，Andrew S. Tanenbaum（MINIX作者，操作系统权威教授）在comp.os.minix上发表了著名的"LINUX is obsolete"帖子：

> "LINUX is a monolithic style system. To me, writing a monolithic system in 1991 is a truly poor idea."

Tanenbaum的核心论点：
1. 微内核是未来趋势——模块化、可移植、更安全
2. Linux是"倒退到1970年代"的单内核设计
3. Linux过于紧密绑定x86架构，"到2000年x86就会被淘汰"

### Linus的反驳逻辑

Linus的回应基于几个层面：

1. **实用主义**: "理论上微内核更好，但Linux现在已经能跑在实际硬件上，MINIX在哪里？"
2. **性能**: 微内核的IPC开销在实际中不可接受
3. **"代码胜于雄辩"**: Linux是工作的代码，不是学术论文
4. **架构选择是刻意的**: 对386特性的深度利用是设计选择不是无知——"It uses every conceivable feature of the 386 I could find"

### 辩论参与者

David Miller（后来成为主要内核贡献者）、Ken Thompson（Unix创始人之一）也参与了讨论，使这场辩论成为操作系统历史上的标志性事件。

### 事后反思

- Linus在多年后被问及辩论时强调他对Tanenbaum无任何敌意，甚至最初不允许O'Reilly收录辩论，直到被说服这会展示当时操作系统设计的思潮
- Tanenbaum后来也声明："we may disagree on some technical issues, but that doesn't make us enemies"
- 现实中Linux后来演变为事实上的 **混合内核**（可加载内核模块、FUSE等），部分验证了双方都有道理
- "x86会被替代"的预测完全落空——x86成为历史上最成功的处理器架构

### 言行一致性分析

- **一致**: Linus的"做出来再说"哲学贯穿始终——不事先争论理论，用工作代码证明
- **有趣演变**: Linux后来吸收了很多微内核思想（模块化、FUSE用户空间文件系统），但Linus从不承认这是向谭教授"投降"——他只是采纳任何被证明有效的技术方案
- **一致性案例**: 从1992年到今天，Linus始终坚持"代码质量>学术正确"的评判标准

**来源**:
- "Appendix A - The Tanenbaum-Torvalds Debate", O'Reilly Open Sources, https://www.oreilly.com/openbook/opensources/book/appa.html [可信度: High - 收录了完整原始帖子]
- OSNews总结, https://www.osnews.com/story/14612/tanenbaum-torvalds-debate-part-ii [可信度: Medium-High]
- Matt Rickard分析, https://mattrickard.com/tanenbaum-torvalds-debates-part-1 [可信度: Medium]

---

## 五、C++ vs Rust争议中的立场

### 对C++的彻底拒绝（2004-2007年）

**2004年**——内核C++模块讨论：

> "In fact, in Linux we did try C++ once already, back in 1992. It sucks. Trust me - writing kernel code in C++ is a BLOODY STUPID IDEA."

核心论点：
- "the whole C++ exception handling thing is fundamentally broken. It's especially broken for kernels."
- C++编译器不可信——在背后隐藏内存分配
- 可以在C中写面向对象代码，"without the crap that is C++"

**2007年**——Git使用C的著名长篇抨击（回复Dmitry Kakurin建议Git用C++）：

> "C++ is a horrible language. It's made more horrible by the fact that a lot of substandard programmers use it... Quite frankly, even if the choice of C were to do *nothing* but keep the C++ programmers out, that in itself would be a huge reason to use C."

完整论点：
- C++导致糟糕的设计选择（STL、Boost等"total and utter crap"）
- 抽象层两年后成为性能瓶颈但代码已深度依赖，无法重构
- 唯一写出高效可移植C++的方法是限制自己只用C已有的特性
- C++程序员整体质量差——"any programmer that would prefer the project to be in C++ over C is likely a programmer that I really would prefer to piss off"

### 2022年：C++尝试在两周内被放弃

在2022年Open Source Summit上，Linus透露：
> "We tried C++ 25 years ago. We tried it for two weeks. And then we stopped trying it."

### 对Rust的开放但谨慎的立场（2020-2025年）

**2022年Open Source Summit**：Linus预测Rust可能在2023年或"maybe the next release"进入主线内核。

关键差异理由：
- Rust不是C++——它解决了C++没有解决的问题（内存安全）
- "C++ solves *none* of the C issues, and only makes things worse" vs Rust实际解决内存安全问题
- Rust采取务实路径——专有维护者（Rust-for-Linux子项目），不强制现有C维护者学习Rust

**2025年争议（Hellwig对抗）**：
- Christoph Hellwig（DMA子系统维护者）反对Rust代码进入其子系统
- Linus介入：Rust不会被强制强加于不愿配合的维护者，但也不会被个别维护者完全阻止
- 最终立场："Maybe the problem is you"——建议不合作的维护者可以fork自己的内核

### 言行一致性分析

- **高度一致**: 对C++的批评基于工程现实（异常处理、隐藏内存分配、过度抽象），对Rust的开放也基于工程现实（实际解决安全问题）
- **核心原则不变**: 工具是为工程服务的——C++不能服务内核工程，Rust可能可以
- **不一致的表象**: 表面看起来"讨厌C++却接受Rust"是双标，但Linus的评判标准从未改变——技术优点决定一切
- **一致性体现**: 他对Rust的态度同样谨慎——不会一夜之间重写内核，"people don't understand Rust...We will have maintainers for the Rust parts"

**来源**:
- Linus Torvalds on C++ (2007年Git邮件列表), harmful.cat-v.org, https://harmful.cat-v.org/software/c++/linus [可信度: High - LKML原文]
- Linus Torvalds on C++ (2004年内核邮件), 同上 [可信度: High]
- Open Source Summit 2022, The New Stack报道, https://thenewstack.io/rust-in-the-linux-kernel-by-2023-linus-torvalds-predicts [可信度: High]
- "Maybe the problem is you", The Register, 2025年2月, https://forums.theregister.com/forum/all/2025/02/07/linus_torvalds_rust_driver [可信度: Medium-High]

---

## 六、离开Transmeta的决策（2003年6月）

### 背景

- 1996年Linus接受Transmeta邀请搬到加州——一家设计低功耗CPU的初创公司
- 在Transmeta工作了6年多（1997-2003）
- Transmeta一直极其支持他的Linux工作，允许他花大量时间在内核上

### 决策逻辑

2003年6月17日，Linus在LKML上宣布离开：

> "I've decided to take a leave-of-absence after 6+ years at Transmeta to actually work full-time on the kernel."

> "Transmeta has always been very good at letting me spend even an inordinate amount of time on Linux, but as a result I've been feeling a little guilty at just how little 'real work' I got done lately."

核心动机：
1. **内疚感**——在Transmeta的实际工作产出太少
2. **Linux需要全职投入**——内核已成长为庞大的协作项目
3. **OSDL的机会**——Open Source Development Lab（Linux基金会的前身）提供了专门为Linux工作的职位

### OSDL的支持

- 非营利组织，由IBM、HP、Intel、AMD、Red Hat、Nokia等公司赞助
- Larry Augustin帮助安排了赞助事宜
- Linus终于可以"finally actually doing Linux as my main job"

### Linus的情感表达

> "Snif. I'm actually all teary-eyed." — LKML邮件结尾

### 事后反思

- Transmeta后来未能成功（低功耗CPU市场未如其预期发展），Linus在正确的时间离开了
- OSDL后来与Free Standards Group合并成为 **Linux Foundation**，Linus至今仍是LF Fellow
- 这次决策使Linus从"业余项目维护者"转变为"全职开源领袖"，是Linux职业化的关键转折点

### 言行一致性分析

- **高度一致**: 决策逻辑完全透明——公开表达感激和内疚，解释为什么离开
- **工程优先**: "real work"定义为写代码和管内核，而非公司政治或管理

**来源**:
- "Linus Torvalds leaves Transmeta", Linux.com, 2003年6月17日, https://www.linux.com/news/linus-torvalds-leaves-transmeta-work-full-time-linux [可信度: High - 引用LKML原文]
- "Linus Torvalds leaves Transmeta", The Register, 2003年6月17日, https://www.theregister.com/software/2003/06/17/linus-torvalds-leaves-transmeta/831245 [可信度: High]
- Computer History Museum profile, https://computerhistory.org/profile/linus-torvalds [可信度: High]

---

## 七、2018年道歉与行为准则变革

### 背景与触发

多年来Linus因在LKML上的攻击性言辞而臭名昭著。典型案例：
- "Please just kill yourself now. The world will be a better place."
- "SHUT THE FUCK UP!"
- 计算机教授Megan Squire分析21000封邮件发现：超过1000次使用"crap"

**直接触发**:
- 2018年Maintainer Summit因Linus错误预订了苏格兰假期导致从温哥华紧急改到爱丁堡
- 这意味着Linus甚至不打算出席峰会——一个明显的警告信号
- 《The New Yorker》杂志正在准备一篇关于他行为的深度报道

### 道歉内容（2018年9月16日，LKML）

Linus在4.19-rc4发布邮件中写道：

> "This week people in our community confronted me about my lifetime of not understanding emotions. My flippant attacks in emails have been both unprofessional and uncalled for. Especially at times when I made it personal. In my quest for a better patch, this made sense to me. I know now this was not OK and I am truly sorry."

> "I need to change some of my behavior, and I want to apologize to the people that my personal behavior hurt and possibly drove away from kernel development entirely."

关键行为：
1. **暂停内核维护**——Greg Kroah-Hartman接手4.19发布
2. **寻求专业帮助**——"get some assistance on how to understand people's emotions and respond appropriately"
3. **类比Git时刻**——将此比作当年停内核开发去写Git的另一类必需的暂停
4. **内核采纳行为准则**——从"code of conflict"（代码质量第一）转为正式的Code of Conduct

### 之前几年Linus对自己行为的辩护（2013-2015）

2013年回复Sage Sharp要求他停止辱骂时：
> "If you want me to 'act professional,' I can tell you that I'm not interested. I'm sitting in my home office wearing a bathrobe...I'm also not going to buy into the fake politeness, the lying, the office politics and backstabbing."

2015年：
> "I don't care about you."

### 事后影响（2018年至今）

**短期**:
- 6周后Linus返回内核维护
- 行为确实发生了一定改变——邮件中的辱骂和人身攻击显著减少
- 技术性批评仍然严厉，但更少涉及人身攻击

**长期**:
- CoC的采纳标志着Linux内核从"技术精英俱乐部"向"专业化协作社区"的转型
- 女性和少数群体开发者反馈有所改善但仍有很长的路要走（当时女性贡献者约10%）
- Sage Sharp和Valerie Aurora等前贡献者对此持"wait and see"态度
- Matthew Garrett（长期批评者）称其为"long overdue step in the right direction"，但强调"believe it when I see some actual change"

### 言行一致性分析

- **重大转折**: 这是Linus言行从"我不在乎你怎么想"到"我意识到伤害了别人"的最大转变
- **一致的内核**: 即使道歉，他仍将其框定为"修复我的工具和工作流"的工程问题——与Git时刻的类比揭示了他将人际问题也视为可修复的系统问题的思维模式
- **部分不一致**: 曾经多年激烈辩护自己的行为，然后突然转向——但触发因素更多是社区压力和机构压力（CoC、峰会、媒体报道）而非内心顿悟

**来源**:
- Linus Torvalds LKML道歉帖, 2018年9月16日, https://lkml.org/lkml/2018/9/16/167 [可信度: High - 原始邮件]
- "Linus Torvalds apologizes for years of being a jerk", Ars Technica, 2018年9月, https://arstechnica.com/gadgets/2018/09/linus-torvalds-apologizes-for-years-of-being-a-jerk-takes-time-off-to-learn-empathy [可信度: High]
- "After Years of Abusive E-mails, the Creator of Linux Steps Aside", The New Yorker, 2018年, https://www.newyorker.com/science/elements/after-years-of-abusive-e-mails-the-creator-of-linux-steps-aside [可信度: High]
- CNBC报道, https://www.cnbc.com/2018/09/17/linux-creator-linus-torvalds-takes-time-off-apologizes-for-behavior.html [可信度: High]
- Jono Bacon分析, https://www.jonobacon.com/2018/09/16/linus-his-apology-and-why-we-should-support-him [可信度: Medium-High]

---

## 八、Linux基金会技术顾问委员会（TAB）与治理角色的演变

### 背景：TAB的起源

- 2004年内核峰会上，开发者要求社区在OSDL（LF前身）董事会上有代表
- 2006年，首届TAB成立，为内核社区提供与产业赞助方同等的发声权
- Linus作为LF Fellow，自然深度参与TAB事务

### 2018年后治理角色的微妙变化

2018年道歉和短暂离开后，Linus的治理参与方式发生了可观察的变化：

1. **2018年的"不想参加峰会"信号**：Linus错误安排假期导致峰会改址，他承认自己"不想参加"——这表明即使道歉之前，他已对社区治理感到疲惫

2. **从"独裁者"到"最终仲裁者"的语义转变**：Linus的BDFL角色在2018年后更多被描述为"最终集成者"（final integrator）而非"仁慈独裁者"

3. **2024年合同续签引发的连续性规划**：Linus与Linux Foundation的上一份合同在2024年Q3到期，这引发了TAB对"万一Linus不再可用"的正式讨论

### 连续性规划（Conclave文档）- 2025-2026年

2025年底的Maintainer Summit（东京），Dan Williams起草了"Linux Kernel Continuity Document"，Codename **"Conclave"**（教皇选举会议）。

核心机制：
- Linus不再可用/无法履行职责后的72小时内召开会议
- 参与者：最近一次Maintainer Summit受邀者 + TAB成员
- TAB Chair作为后备召集人
- 不指定单一继承人，而是选定"一个或多个人"管理顶级仓库
- 可能转向分布式领导模型（group/council）

### Linus对退休的态度

> "My plan seems to just be 'I will live forever.'" — Linus Torvalds

> "Perhaps equally importantly, my wife doesn't want to be pestered by a bored husband."

同时他也承认：
> "Before Greg, there was Andrew Morton and Alan Cox. After Greg, there will be Shannon and Steve. The real issue is you have to have a person or a group of people that the development community can trust."

### 治理决策的核心矛盾

Linus的角色演变揭示了一个基本张力：
- **技术决策**: 他仍然是所有补丁的最终仲裁者（2025年仍在签署约1/3的提交）
- **社区治理**: 他越来越倾向于将"政治性"事务委托给TAB和其他机构
- **定位**: 从"我们不需要行为准则"到接受CoC，从抵制反馈到接受"需要帮助"，再到为"没有我的世界"做规划

### 言行一致性分析

- **持续一致**: Linus从未想要成为治理者——"I do software, and I license software"——他始终将自己定位为工程师而非政治领袖
- **持续一致**: 对TAB的态度是实用主义——它是一个需要存在的机制，但最好在幕后运作，不影响实际代码工作
- **有趣演变**: 2018年前Linus拒绝任何形式的程序化治理，现在他签署了Conclave文档，承认"bus-factor of one"是不可持续的——但他将此视为工程问题（冗余和故障转移），而非权力交接

**来源**:
- "Linux after Linus? The kernel community finally drafts a plan for replacing Torvalds", ZDNet (Steven Vaughan-Nichols), 2026年1月, https://www.zdnet.com/article/linux-community-project-continuity-plan-for-replacing-linus-torvalds [可信度: High - 直接引用Linus和关键维护者原话]
- "An open seat on the TAB", LWN.net (Jonathan Corbet), 2025年12月, https://lwn.net/Articles/1049035 [可信度: High - TAB资深成员第一手叙述]
- "Linux Kernel Continuity Document Added", Phoronix, 2026年1月, https://www.phoronix.com/news/Linux-Kernel-Continuity-Doc [可信度: High]
- "Linux Kernel Quietly Formalizes What Happens If Torvalds Steps Away", Linuxiac, 2026年1月, https://linuxiac.com/linux-kernel-formalizes-what-happens-if-torvalds-steps-away [可信度: Medium-High]

---

## 综合模式分析

### 贯穿所有决策的核心原则

1. **工程实用主义 > 意识形态**: 从选BitKeeper（闭源但好用）到拒绝GPLv3（实用的自由vs.绝对的自由），始终选择对工程最优方案
2. **"代码胜于辩论"**: 从Tanenbaum论战到Git的诞生，Linus用工作代码而非论文证明观点
3. **"技术优点决定一切"**: 对C++彻底拒绝 vs 对Rust有条件接受，评判标准始终是技术能力而非个人喜好
4. **"我只控制我创造的东西"**: 从GPLv2到DRM立场，自我设限于软件，拒绝将软件许可证作为控制硬件的武器
5. **"用完就放手"**: Git写完就交出去，TAB让专业人士管理，内核子系统委托给维护者——聚焦于自己最擅长的事

### 言行一致的典型模式

- **短期一致性**: 在具体技术决策上高度一致（C++不行就是不行，20年后也未改口）
- **长期演变**: 在文化/人际问题上发生了最大转变（从"I don't care about you"到道歉）
- **框架一致**: 即使道歉，仍将其看作"修复工具和工作流"的工程问题，而非道德觉醒

### 言行不一致的案例

1. **"Won't be big" → 世界最大OS项目**: 最初预测与最终结果的巨大反差
2. **"I'm not interested in acting professional" → 2018年道歉**: 对行为准则的立场180度转变
3. **"I don't care about you" → "I am truly sorry"**: 从公开蔑视情感到承认需要理解情绪
4. **"Linux is NOT portable" → 运行在几乎所有架构上**: 最初的设计选择和后来的普遍可移植性

---

## 方法论说明

- 排除来源：知乎、微信公众号、百度百科
- 优先来源：Linus本人邮件/帖子 > 专业开源媒体（LWN, Ars Technica, The Register）> 主流科技媒体（CNBC, ZDNet, The New Yorker）> 第三方分析
- 所有引用均标注URL和可信度评级的依据
