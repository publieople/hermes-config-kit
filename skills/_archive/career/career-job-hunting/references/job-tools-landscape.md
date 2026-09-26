# Job Hunting Tools & Platforms Reference

## Job Platforms (China, Tech Roles)

| Platform | URL | Best For | Notes |
|----------|-----|----------|-------|
| **BOSS直聘** | zhipin.com | ⭐⭐⭐ General tech internships | Most active, chat-first model, 150 hellos/day |
| **实习僧** | shixiseng.com | ⭐⭐⭐ Internship-specific | Dedicated intern listings, AI matching |
| **牛客网** | nowcoder.com | ⭐⭐ Interview prep + jobs | Algorithm practice,面经, 内推码 |
| **拉勾** | lagou.com | ⭐⭐ Tech-focused | Good for internet companies |
| **猎聘** | liepin.com | ⭐ Mid-to-senior | More experienced positions |
| **智联招聘** | zhaopin.com | ⭐ General | Broad coverage, less tech-focused |
| **前程无忧** | 51job.com | ⭐ General | Traditional CV platform |
| **脉脉** | maimai.cn | ⭐⭐ Networking | Company reviews, internal referrals |
| **上海人工智能实验室** | shlab.org.cn | ⭐⭐ Research/PhD track | Internship + campus recruitment |
| **百度校招** | talent.baidu.com | ⭐⭐ Big tech | 日常实习不限毕业时间 |

## Auto-Apply / AI-Assisted Tools

| Tool | Stars | Language | Platforms | Deployment | Notes |
|------|-------|----------|-----------|------------|-------|
| **get_jobs** (loks666) | >6k | Java/Gradle | BOSS, 前程无忧, 猎聘, 智联 | JDK21 + Maven + ChromeDriver | Most popular, Windows-oriented, AI greeting + blacklist + daily limits |
| **牛人快跑** (geekgeekrun) | Active | Puppeteer/Electron | BOSS only | Desktop app (.exe/.dmg/.deb) | GUI, auto-chat + re-chat + zombie cleanup |
| **boss_batch_push** (yangfeng20) | Active | JS script | BOSS only | Browser script (Tampermonkey) | Lightweight, word cloud, filtering |
| **JobClaw** (slothsheepking) | New | Python/Playwright | BOSS, LinkedIn | pip install | LLM match + auto-apply + Telegram/Discord notifications |
| **mcp-jobs** (mergedao) | NPM | Node.js/Playwright | 猎聘, BOSS, 智联, 51job | npx or npm install | MCP protocol, search/aggregation only, zero config |

## AI Resume/CV Tools

| Tool | URL | Use Case |
|------|-----|----------|
| **visiky/resume** | visiky.github.io/resume | Online resume generator (Gatsby + JSON config) |
| **求职方舟AI** | qiuzhifangzhou.com | AI search + rewrite + auto-fill applications |
| **塔塔网申** | tatawangshen.com | Auto-fill enterprise application forms |

## Job Search Data Analysis

| Tool | Language | Purpose |
|------|----------|---------|
| **boss_zhipin_pachong** (ctkqiang) | Spring Boot + SQLite | BOSS data crawler + salary/skill trend analysis |
| **lagou-spider-node** (SunshowerC) | Node.js | 拉勾 position crawler |