# colleges.chat 学校拼音查找表

colleges.chat 的 URL 格式：`https://colleges.chat/universities/<拼音>/`

## 常见命名规律

### 规则 1：全称小写拼音，`-` 连接
- 北京大学 → bei-jing-da-xue
- 上海师范大学 → shang-hai-shi-fan-da-xue
- 延边大学 → yan-bian-da-xue
- 天津工业大学 → tian-jin-gong-ye-da-xue

### 规则 2：异体/缩写
- 南京林业大学淮安校区 → nan-jing-lin-ye-da-xue-huai-an-xiao-qu
- 中国地质大学(武汉) → zhong-guo-di-zhi-da-xue-wu-yi（注意 wu-yi 不是 wu-han！）
- 中国地质大学(北京) → zhong-guo-di-zhi-da-xue-bei-jing
- 广州中医药大学 → yan-zhou-zhong-yi-yao-da-xue（注意 yan-zhou 是"广州"传统译法）

### 规则 3：部分学校用英文
- THU / PKU / NJU / Fudan 等

### 规则 4：分校区/实验区不一定有独立页面
- 部分高校的分校区单独列页面（如南京林业大学淮安校区）
- 中外合作办学/新建校区/国际教育实验区**不一定**有独立指北页面
- 示例：中国传媒大学海南陵水校区 → 指北只有北京主校区页面，无海南信息

### 已知正确拼音（session积累）
- 中国矿业大学（徐州）→ zhong-guo-kuang-ye-da-xue（注意首次 curl 可能 000/35 非 404，重试即可 200）
- 中国矿业大学(北京) → zhong-guo-kuang-ye-da-xue-bei-jing
- 部分高校的分校区单独列页面（如南京林业大学淮安校区）
- 中外合作办学/新建校区/国际教育实验区**不一定**有独立指北页面
- 示例：中国传媒大学海南陵水校区 → 指北只有北京主校区页面，无海南信息

### 名称不再严格反映学校（拼音≠当前名称，要靠 page title 确认）
URL 路径名 ≠ 当前期望的校名。**拿到 URL 后直接 `browser_navigate` 一次看 `<title>` 字符串**——多数情况下能消除歧义，再决定继续抓哪里。

- `zhu-bo-da-xue/` → 实际是**宁波大学**（zh-u-bo 拼写），不是"淄博大学"（淄博无"淄博大学"高校）
- 警惕任何 pinyin 路径走"语义上看着不像目标"的页面：可能是 colleges.chat 历史 slug 路由 / 镜像页 / 实验页面 — 永远以页面 `<title>` 为准。

## 快速定位方法

**不确定拼音时**，先搜：`site:colleges.chat/universities 学校名`

## 代理说明

colleges.chat 在国内服务器，从 WSL 直接访问会 ERR_CONNECTION_RESET。需通过 Clash 代理：
```bash
curl -sL -x http://127.0.0.1:7890 "https://colleges.chat/universities/<拼音>/"
```
