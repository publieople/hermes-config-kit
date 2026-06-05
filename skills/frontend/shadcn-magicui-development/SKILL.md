---
name: shadcn-magicui-development
description: "Build UI with shadcn/ui + magicui: setup, component selection, interactive effects (MagicCard, OrbitingCircles, Typewriter), card design patterns, reference site analysis, build-verify-deploy"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [frontend, ui, react, nextjs, tailwind, shadcn, magicui, homepage, portfolio, interactive]
    related_skills: [writing-plans, spec-kit-greenfield-init, ui-ux-pro-max]
---

# shadcn/ui + magicui 前端开发

## 触发条件

当用户要求以下操作时加载本 skill：
- 搭建/修改个人主页、作品集、落地页
- 添加 shadcn/ui 或 magicui 组件
- 分析参考网站的交互效果和技术实现
- 在前端项目中使用 Tailwind CSS v4 + shadcn/ui + magicui

## 技术栈约定

```
Next.js (App Router) + TypeScript
Tailwind CSS v4
shadcn/ui (new-york style)
magicui (via `npx shadcn@latest add @magicui/<component>`)
framer-motion (动画)
```

### 组件安装

所有组件通过 shadcn CLI 安装，不要手写替代实现：

```bash
# shadcn/ui 组件
npx shadcn@latest add button card avatar badge

# magicui 组件
npx shadcn@latest add @magicui/particles
npx shadcn@latest add @magicui/bento-grid
npx shadcn@latest add @magicui/typing-animation
npx shadcn@latest add @magicui/animated-gradient-text
```

**核心原则：** 有现成的 magicui 组件就用现成的——别人专门维护的比自己手写的靠谱。只在 magicui 不能满足需求时编写自定义实现。

### magicui 常用组件速查

| 效果 | 组件 | 安装命令 |
|------|------|---------|
| 粒子背景 | `Particles` | `npx shadcn@latest add @magicui/particles` |
| Bento Grid 布局 | `BentoGrid` + `BentoCard` | `npx shadcn@latest add @magicui/bento-grid` |
| 打字机效果 | `TypingAnimation` | `npx shadcn@latest add @magicui/typing-animation` |
| 渐变文字 | `AnimatedGradientText` | `npx shadcn@latest add @magicui/animated-gradient-text` |
| 光标动画 | `TextAnimate` | `npx shadcn@latest add @magicui/text-animate` |
| 主题切换动画 | `AnimatedThemeToggler` | `npx shadcn@latest add @magicui/animated-theme-toggler` |

### TypingAnimation 组件配置

`TypingAnimation` 支持两种模式：

1. **单行打字（children）** — 逐个字符打出，一次性不循环
2. **多词轮换（words 数组）** — 打字 → 停顿 → 删除 → 下一词，可循环

推荐配置（博客式打字机效果）：
```tsx
<TypingAnimation
  words={["词1", "词2", "词3"]}   // 多词轮换
  duration={120}                    // 打字速度(ms/字)，默认100
  pauseDelay={2000}                 // 打完后的停顿(ms)
  loop={true}                       // 循环
  startOnView={false}               // 立即开始(true=滚动到视口才开始)
  showCursor={true}                 // 显示闪烁光标
  cursorStyle="line"                // line | block | underscore
/>
```

## Proven Patterns (English reference)

These are battle-tested component patterns for pages using shadcn/ui + magicui + framer-motion.

### Hero Section (Particles + Gradient Title + Avatar)

```tsx
import { Particles } from "@/components/ui/particles";
import { AnimatedGradientText } from "@/components/ui/animated-gradient-text";
import { motion } from "framer-motion";

<section className="relative overflow-hidden">
  <Particles
    className="absolute inset-0"
    quantity={80}
    color="#533afd"
    vx={0.1}
    vy={0.1}
  />
  {/* Gradient overlay for readability */}
  <div className="absolute inset-0 bg-gradient-to-b from-background/70 via-background/30 to-background pointer-events-none" />

  <div className="relative z-10">
    <motion.div
      whileHover={{ scale: 1.08, rotate: -3 }}
      transition={{ type: "spring", stiffness: 300, damping: 12 }}
    >
      <Avatar className="ring-2 ring-primary/20 hover:ring-primary/50 hover:shadow-[0_0_30px_-5px] hover:shadow-primary/30">
        <AvatarImage src="/avatar.jpg" alt="..." />
      </Avatar>
    </motion.div>

    <AnimatedGradientText speed={2} colorFrom="#533afd" colorTo="#ec4899">
      人民公仆
    </AnimatedGradientText>
  </div>
</section>
```

### Bento Grid for Projects

```tsx
import { BentoGrid } from "@/components/ui/bento-grid";

<BentoGrid className="grid-cols-1 md:grid-cols-3 auto-rows-auto gap-4 md:gap-5">
  {/* Large card: spans 2 cols, 2 rows */}
  <motion.div className="md:col-span-2 md:row-span-2" ...>
    <div className="h-full rounded-xl border bg-card hover:-translate-y-1 hover:shadow-[0_0_25px_-3px] hover:shadow-primary/20 hover:border-primary/30 transition-all duration-300">
      {/* card content */}
    </div>
  </motion.div>

  {/* Small cards: span 1 col */}
  <motion.div className="md:col-span-1" ...>
    <div className="h-full rounded-xl border bg-card ...">
      {/* card content */}
    </div>
  </motion.div>
</BentoGrid>
```

### Consistent Hover Effects

All card-type elements should share the same hover language:

```tsx
className="transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_0_20px_-3px] hover:shadow-primary/15 hover:border-primary/30"
```

### Scroll Animations

```tsx
<motion.div
  initial={{ opacity: 0, y: 30 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true, margin: "-80px" }}
  transition={{ duration: 0.6 }}
>
```

For staggered cards: `transition={{ duration: 0.5, delay: i * 0.1 }}`

### Scroll Parallax (Hero Fade-out)

Use `useScroll` + `useTransform` to create a parallax fade-out as the user scrolls past the Hero section:

```tsx
import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";

export function Hero() {
  const sectionRef = useRef<HTMLElement>(null);

  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ["start start", "end start"],
  });
  const contentOpacity = useTransform(scrollYProgress, [0, 0.35, 0.7], [1, 1, 0]);
  const contentY = useTransform(scrollYProgress, [0, 0.7], [0, -60]);

  return (
    <section ref={sectionRef} className="relative min-h-screen overflow-hidden">
      <motion.div style={{ opacity: contentOpacity, y: contentY }}>
        {/* Hero content — fades and drifts up on scroll */}
      </motion.div>
    </section>
  );
}
```

**Key notes:**
- `offset: ["start start", "end start"]` — maps scroll progress from "top of section at viewport top" to "bottom of section at viewport top"
- `useTransform` creates a MotionValue that binds directly to `style` — no re-renders on scroll
- Inner mount animations (`initial/animate`) compose correctly with MotionValue styles: mount animation runs once, then scroll takes over
- The fade should complete before the section fully leaves viewport (0→0.7 range) so the next section's `whileInView` entrance overlaps smoothly

### Scroll Indicator (Hero bottom)

```tsx
<div className="relative">
  <div className="absolute inset-0 rounded-full animate-ping bg-primary/20" />
  <ArrowDown className="relative size-4 animate-bounce" />
</div>
```

## Magicui Component Quick Reference (English)

| Component | Import | Key Props |
|-----------|--------|-----------|
| Particles | `@/components/ui/particles` | `quantity`, `color` (hex), `vx`, `vy`, `staticity`, `ease` |
| AnimatedGradientText | `@/components/ui/animated-gradient-text` | `colorFrom`, `colorTo`, `speed` |
| BentoGrid | `@/components/ui/bento-grid` | children + `className` for grid layout |
| BentoCard | `@/components/ui/bento-grid` | `name`, `description`, `Icon`, `background`, `href`, `cta`, `className` |
| AnimatedThemeToggler | `@/components/ui/animated-theme-toggler` | (View Transitions API based) |
| MagicCard | `@/components/ui/magic-card` | simple card with hover glow |

## 图标 sourcing 策略

自定义图标有明确的 sourcing 优先级，不要手写 SVG：

1. **品牌图标** → `@lobehub/icons`（如 `HermesAgent`, `Notion`, `OpenClaw`, `Github`, `ComfyUI`）
2. **通用品牌** → `@icons-pack/react-simple-icons`（如 `SiArchlinux`, `SiDocker`, `SiBilibili`, `SiGithub`）
3. **通用 UI 图标** → `lucide-react`（如 `Terminal`, `Globe`, `BookOpen`, `ArrowDown`）
4. **特殊专用图标** → 官网下载 SVG 转 React 组件（如 `QuickerIcon`, `AdobePhotoshopIcon` — 仅在 1-3 找不到时）

**迁移模式：** 已有手写 SVG 要替换时，保持组件名不变，内部改为 re-export：

```tsx
// github-icon.tsx — 从手写 SVG 迁移到 simple-icons
import { SiGithub } from "@icons-pack/react-simple-icons";
export function GithubIcon({ className }: { className?: string }) {
  return <SiGithub className={className} />;
}
```

这样所有 import 该组件的地方自动生效，零改动。

**验证：** `npm run build` 通过后打开页面，确认图标样式（大小、颜色、对齐）与替换前一致。

## Theme System

- `data-theme` — visual style (e.g., "stripe"). CSS variables in `:root[data-theme="xxx"]`
- `data-mode` — light/dark. CSS variables in `:root[data-theme="xxx"][data-mode="dark"]`
- Both persisted to localStorage to prevent FOUC (inline script in `<head>`)
- Mode toggle uses View Transitions API for clip-path circle reveal animation

## 开发工作流

### Step 0: 生成设计系统（绿色项目必做）

在任何代码编写之前，先用 `ui-ux-pro-max` 生成完整设计系统。不要跳过这一步——直接跳到编码会导致配色/字体/风格不一致。

```bash
cd ~/.hermes/skills/openclaw-imports/ui-ux-pro-max-skill/src/ui-ux-pro-max
python3 scripts/search.py "<产品描述 行业 关键词>" --design-system -p "项目名称" -f markdown
```

`ui-ux-pro-max` 的输出包含：
- **Style** — 产品风格（暗黑/玻璃/极简等）
- **Colors** — 语义化配色方案（primary/secondary/accent/background/foreground）
- **Typography** — 字体搭配方案（含 Google Fonts 导入链接）
- **Effects** — 关键效果建议（发光/扫描线/毛玻璃等）
- **Anti-patterns** — 明确告知避免什么

根据输出结果配置 `globals.css` 的 CSS 变量（`:root` 和 `.dark` 的色值），并在 `layout.tsx` 中配置对应字体。

**何时可以跳过：** 仅当项目已由用户指定了完整的设计规范（精确色值、字体、边距）时。

完整多 skill 管线参考：`references/greenfield-multi-skill-workflow.md`

### Homepage Redesign Workflow

When the user asks to redesign or improve an existing homepage, follow this research-driven proposal workflow:

1. **Research current trends** &mdash; Search for award-winning portfolio sites, bento grid designs, card patterns from 2025-2026. See `references/portfolio-design-research-2026.md` for collected references.
2. **Analyze current state** &mdash; Read all section components, globals.css, SPEC/PLAN files. Identify specific problems per section.
3. **Propose with before/after** &mdash; Structured proposal with per-section comparison, specific Tailwind class changes, guarantee of zero new npm deps, guarantee of `npm run build` passing.
4. **Wait for explicit approval** before implementing.
5. **Execute incrementally** &mdash; One section at a time, verify build after each batch.

### Step 1: 规划

参考 `writing-plans` skill，先制定方案获得审批再实施：

```
方案 → 审批？→ 实施 → 验证(build) → 推送(deploy)
```

### Step 2: 参考网站分析

当用户要求参考某网站时，系统化逆向分析其交互效果：

#### 2.1 技术栈识别
```js
// 检查框架
document.querySelectorAll('script[src]').map(s=>s.src)
// 检查CSS框架
document.querySelectorAll('link[rel=stylesheet]').map(l=>l.href)
// 检查Next.js数据
window.__NEXT_DATA__
```

#### 2.2 CSS 动画提取
拉取 CSS bundle，搜索关键动画和组件样式：
- `@keyframes` — 自定义动画（pulse, orbit, scroll, fade-in 等）
- 自定义组件类名（tilt, card, accent 等）
- 3D 变换设置（`transform-style: preserve-3d`, `perspective`）

#### 2.3 JS 交互逻辑逆向

拉取主 JS bundle（`chunks/pages/index-*.js` 或 `chunks/app/layout-*.js`），搜索：
- React hooks：`useEffect`, `useState`, `useRef`, `useContext`
- 动画库引用：`framer-motion`, `motion`, `gsap`, `spring`
- CSS-in-JS 变换：`style.transform`, `translateX`, `rotateY`, `perspective`
- 事件追踪：`mouseEnter`, `mouseMove`, `IntersectionObserver`
- 数字格式化：`Intl.NumberFormat`, `toLocaleString`
- 滚动检测：`useScroll`, `useInView`, `scrollY`
- 弹簧动画：`useSpring`, `damping`, `stiffness`, `useSpringValue`

#### 2.4 DOM 结构检查
```js
// 查看交互元素的 class、style、事件
Array.from(document.querySelectorAll('li')).slice(0,3).map(el => ({
  classes: Array.from(el.classList),
  transition: getComputedStyle(el).transition,
  transform: getComputedStyle(el).transform,
}))

// 检查 Tailwind group hover 模式
document.querySelectorAll('.group, [class*=" group"]').length

// 查找计数器等动态内容
document.querySelectorAll('strong').forEach(s => console.log(s.textContent))
```

#### 2.5 运行时观察
```js
// 检查动态内容是否变化
const val = element.textContent;
setTimeout(() => console.log('changed:', val !== element.textContent), 500);
```

### Step 3: 实施

参考 `spec-kit-greenfield-init` 的 spec 驱动模式：
1. 写 SPEC（需求规格）
2. 写 PLAN（分阶段实施计划）
3. 按 Phase 逐个实现
4. 每阶段独立验证

### Step 4: 编译验证

```bash
npm run build
# 必须通过，无 TypeScript 错误、无 Lint 错误
```

### Step 5: 部署

```bash
git add -A
git commit -m "Phase X.Y: description"
git push
# Actions 自动部署到 GitHub Pages / Vercel
```

## 常见交互效果实现方案

### 3D Tilt Card（鼠标追踪按压效果）
使用 React Context 追踪鼠标位置 + CSS 3D 变换：
```
MouseEnterProvider (Context)
  → TiltContainer (transform-style: preserve-3d)
    → Tilt (读取鼠标位置，应用 translateX/Y/Z + rotateX/Y/Z)
    → transition: all 200ms ease-linear
```
参考：`references/qzq-at-interactive-effects.md`

**简化版（自包含组件，无需 Context）：**
```tsx
// 直接使用 mouse move event + inline style transform
ref.current.style.transform = `perspective(400px) rotateX(${rx}deg) rotateY(${ry}deg)`;
```
参考：`references/3d-tilt-card.md` — 带完整源码和参数说明。

### 鼠标驱动的 3D Parallax（轨道图标群倾斜）

用于 Hero 区的环绕图标群，鼠标移动时产生 3D 倾斜跟随效果：

```tsx
const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

const handleMouseMove = useCallback((e: React.MouseEvent) => {
  const rect = e.currentTarget.getBoundingClientRect();
  const x = (e.clientX - rect.left) / rect.width - 0.5;
  const y = (e.clientY - rect.top) / rect.height - 0.5;
  setMousePos({ x, y });
}, []);

const handleMouseLeave = useCallback(() => {
  setMousePos({ x: 0, y: 0 });
}, []);

// 在 orbit 容器上使用：
<motion.div
  animate={{
    rotateX: mousePos.y * -12,
    rotateY: mousePos.x * 12,
  }}
  transition={{ type: "spring", stiffness: 150, damping: 20 }}
  style={{ transformStyle: "preserve-3d" }}
>
  {/* OrbitingCircles children */}
</motion.div>
```

**关键点：**
- `useCallback` 防抖不如 spring 阻尼有效 — spring 的 `damping: 20` 本身提供平滑手感
- `mousePos.y * -12` 的负号让倾斜方向符合直觉：鼠标左移→向右旋转
- `handleMouseLeave` 重置到 0，防止鼠标离开后保持在奇怪角度
- 父 section 绑定 `onMouseMove` + `onMouseLeave`，而非 orbit 容器本身（扩大感应范围）

### 动画数字计数器（推荐：setInterval + useState）

比 spring 方案更简单可靠，无额外 import：

```tsx
function CountUp({ to, suffix = "" }: { to: number; suffix?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!isInView) return;
    let start = 0;
    const duration = 1000;            // 1s 完成动画
    const step = Math.max(1, Math.ceil(to / (duration / 16))); // ~60fps
    const timer = setInterval(() => {
      start += step;
      if (start >= to) { setCount(to); clearInterval(timer); }
      else { setCount(start); }
    }, 16);
    return () => clearInterval(timer);
  }, [isInView, to]);

  return (
    <div ref={ref}>
      <motion.span
        initial={{ opacity: 0, y: 8 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
      >
        {count}{suffix}
      </motion.span>
    </div>
  );
}
```

**关键点：**
- `useInView` 触发动画开始（`once: true` 只触发一次）
- `margin: "-40px"` 让数字在元素进入视口前就开始动画
- 配合 `tabular-nums` class 防止数字宽度跳动

### 无限滚动 Marquee
1. 克隆子元素用于无缝循环
2. CSS `@keyframes scroll` 控制位移
3. `--animation-duration` 控制速度
4. `hover:[animation-play-state:paused]` 暂停

### 横向 Scroll-Snap 卡片群（Blog 节推荐）

用于替代纵向列表的"文章/内容"展示区：

```tsx
<div className="flex gap-4 pb-4 overflow-x-auto snap-x snap-mandatory scrollbar-hide"
     style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}>
  {/* 左侧间距 */}
  <div className="shrink-0 w-[calc((100vw-48px-80px-16px)/2)] hidden sm:block" />

  {/* 卡片：fixed width + snap-start */}
  <a className="group flex-shrink-0 w-[280px] sm:w-[320px] snap-start">
    <div className="rounded-2xl border border-border/50 bg-card overflow-hidden
                    transition-all duration-300 hover:border-primary/30
                    hover:shadow-[0_0_30px_-8px] hover:shadow-primary/15">
      {/* 渐变头部 */}
      <div className="h-24 bg-gradient-to-br from-blue-500/10 to-purple-500/10
                      flex items-start justify-end p-4">
        <span className="rounded-full bg-blue-500/20 px-2.5 py-0.5
                         text-[10px] font-[500]">{post.meta}</span>
      </div>
      {/* 内容 */}
      <div className="p-5">
        <h3 className="text-sm font-[500]">{post.title}</h3>
        <p className="text-xs text-muted-foreground mt-2">{post.desc}</p>
        {/* 底部进度条 */}
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-muted/50">
          <div className="h-full w-0 bg-primary/30 transition-all duration-700 group-hover:w-full" />
        </div>
      </div>
    </div>
  </a>

  {/* 右侧"查看全部"end card */}
  <a className="group flex-shrink-0 w-[200px] snap-start">
    <div className="h-full rounded-2xl border border-dashed border-border/50
                    flex flex-col items-center justify-center gap-3 p-8">
      <ChevronRight className="size-5 group-hover:scale-110 transition-transform" />
      <span className="text-xs text-muted-foreground/60">查看全部</span>
    </div>
  </a>

  {/* 右侧间距 */}
  <div className="shrink-0 w-[calc((100vw-48px-80px-16px)/2)] hidden sm:block" />
</div>
```

**关键点：**
- `snap-x snap-mandatory` — 强制对齐到最近的卡片
- `snap-start` — 卡片左对齐吸附
- `overflow-x-auto` + `scrollbar-hide` — 隐藏滚动条
- 左右 spacer divs 用 `calc` 居中卡片群
- `hidden sm:block` — 移动端全宽显示，桌面端留边距

### Section 过渡差异化

不要所有 section 用同一个 `whileInView` 入场动画。差异化让滚动节奏更生动：

```tsx
// 在 page.tsx 中定义
const SECTION_VARIANTS = {
  about:    { initial: { opacity: 0, y: 40 }, transition: { duration: 0.6 } },
  projects: { initial: { opacity: 0, x: -30 }, transition: { duration: 0.5 } },
  blog:     { initial: { opacity: 0, x: 30 }, transition: { duration: 0.5 } },
  resume:   { initial: { opacity: 0, y: 40 }, transition: { duration: 0.6 } },
  contact:  { initial: { opacity: 0, scale: 0.95 }, transition: { duration: 0.5 } },
};

function SectionWrapper({ children, variants }) {
  return (
    <motion.div initial={variants.initial}
      whileInView={{ opacity: 1, y: 0, x: 0, scale: 1 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={variants.transition}>
      {children}
    </motion.div>
  );
}
```

**节奏感：** About/Resume 从下往上、Projects/Blog 从左右滑入、Contact 缩放进入。

### Floating Section Nav Indicator

右侧浮动导航圆点，滚动时自动高亮当前 section。

**推荐方案（IntersectionObserver — 更精确、无 scroll 事件抖动）：**

```tsx
"use client";
import { useState, useEffect, useRef } from "react";

const sections = [
  { id: "hero", label: "首页" },
  { id: "about", label: "关于" },
  { id: "projects", label: "项目" },
  { id: "blog", label: "文章" },
  { id: "resume", label: "简历" },
  { id: "contact", label: "联系" },
];

export function SectionNav() {
  const [active, setActive] = useState("hero");
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActive(entry.target.id);
          }
        }
      },
      { rootMargin: "-100px 0px -60% 0px" }
    );

    for (const { id } of sections) {
      const el = document.getElementById(id);
      if (el) observerRef.current.observe(el);
    }

    return () => observerRef.current?.disconnect();
  }, []);

  return (
    <nav className="fixed right-4 top-1/2 -translate-y-1/2 z-40 hidden md:flex flex-col items-center gap-3">
      {sections.map(({ id, label }) => (
        <button
          key={id}
          onClick={() =>
            document.getElementById(id)?.scrollIntoView({ behavior: "smooth" })
          }
          className="group relative"
          aria-label={`跳转到 ${label}`}
        >
          <span className="absolute right-full mr-3 whitespace-nowrap rounded-md
                          bg-muted/90 backdrop-blur px-2 py-1 text-[10px]
                          opacity-0 group-hover:opacity-100 transition-opacity">
            {label}
          </span>
          <span className={`block rounded-full transition-all duration-300 ${
            active === id
              ? "h-2.5 w-2.5 bg-primary shadow-[0_0_8px] shadow-primary/50"
              : "h-1.5 w-1.5 bg-muted-foreground/30 hover:bg-muted-foreground/60"
          }`} />
        </button>
      ))}
      <div className="absolute inset-y-0 left-1/2 -translate-x-1/2
                      w-px bg-gradient-to-b from-transparent via-border/30 to-transparent -z-10" />
    </nav>
  );
}
```

**关键点：**
- `rootMargin: "-100px 0px -60% 0px"` — 顶部 100px 容差避免闪烁，底部 60% 视口才切换激活，确保当前 section 有足够可见面积才高亮
- IntersectionObserver 比 `scroll` 事件更高效，不触发 reflow，且回调不频繁
- 用 `button` + `scrollIntoView({ behavior: "smooth" })` 替代纯 `<a>` 锚点以保留 JS 控制
- 纯 `<a href="#id">` 方案会丢失激活态高亮（无法追踪当前 section）

**备选方案（scroll 事件 — 更简单但精度略低）：**

```tsx
// SectionNav 组件
export function SectionNav() {
  const [active, setActive] = useState("hero");
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY + 120;
      let current = "hero";
      for (const { id } of sections) {
        const el = document.getElementById(id);
        if (el && el.offsetTop <= scrollY) current = id;
      }
      setActive(current);
      setVisible(window.scrollY > window.innerHeight * 0.6);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  if (!visible) return null;

  return (
    <nav className="fixed right-4 top-1/2 -translate-y-1/2 z-40 hidden md:flex flex-col items-center gap-3">
      {sections.map(({ id, label }) => (
        <button key={id} onClick={() => section.scrollIntoView({ behavior: "smooth" })}
                className="group relative" aria-label={`跳转到 ${label}`}>
          {/* Tooltip */}
          <span className="absolute right-full mr-3 whitespace-nowrap rounded-md
                           bg-muted/90 backdrop-blur px-2 py-1 text-[10px]
                           opacity-0 group-hover:opacity-100">{label}</span>
          {/* Dot */}
          <span className={`block rounded-full transition-all duration-300 ${
            active === id
              ? "h-2.5 w-2.5 bg-primary shadow-[0_0_8px] shadow-primary/50"
              : "h-1.5 w-1.5 bg-muted-foreground/30 hover:bg-muted-foreground/60"
          }`} />
        </button>
      ))}
      {/* 连接线 */}
      <div className="absolute inset-y-0 left-1/2 -translate-x-1/2
                      w-px bg-gradient-to-b from-transparent via-border/30 to-transparent -z-10" />
    </nav>
  );
}
```

**注意：** 如果组件放在 Server Component 的 layout.tsx 中但不挂载，先用 `console.log("[SectionNav] mounted")` 验证组件是否到达浏览器。可能的原因：Next.js 的 lazy loading 边界、HMR 未完整刷新。

### 噪点纹理层
```html
<div style="background-image: url(/noise.webp); background-size: 30%"
     class="opacity-10 [mask-image:radial-gradient(#fff,transparent,75%)]" />
```

### 高级交互效果参考

以下效果有更深入的实现细节和陷阱说明，见 `references/interactive-effects-advanced-reference.md`：

- **MagicCard** (mouse-following spotlight) &mdash; Gradient mode, Orb mode, internal architecture, all props
- **ShineBorder** (animated gradient border) &mdash; Installation, configuration, critical nesting restrictions
- **Scroll Progress Bar** &mdash; Zero-config scroll indicator
- **OrbitingCircles positioning & 3D ring** &mdash; Two-bug positioning fix, planetary ring CSS 3D chain, icon sourcing strategy
- **Design philosophy** &mdash; Interactive > Decorative, user preference summary, verification checklist

## Card Design Patterns

Class-level card patterns for bento-grid homepages. See `references/homepage-card-design-patterns.md` for full code examples with accent bars, emoji anchors, sticky footers, and quick facts bars.

### Key Guidelines

- **One card gets a gradient background** (the hero card) &mdash; rest stay flat `bg-card`
- **Hover trifecta** on every card: lift (`hover:-translate-y-1`) + glow (`hover:shadow-[0_0_25px_-3px] hover:shadow-primary/20`) + border color shift (`hover:border-primary/30`)
- **Flex sticky footer** pattern for cards with tags: `flex flex-col h-full` on container, `mt-auto pt-3` on the footer
- **Left accent strip** for blog/article list cards (color-code by category)
- **Project state management** via AGENTS.md at project root &mdash; maintains section-by-section status, design decisions, and roadmap for cross-session resumption

### What to AVOID

- **Static decoration without interactive effects** &mdash; always lead with interactive (MagicCard, ScrollProgress) before static polish
- **Aceternity 3D Card** &mdash; CardBody hardcodes `h-96 w-96`, breaks Bento Grid
- **Nesting ShineBorder inside MagicCard** &mdash; z-index and border-radius conflicts
- **New npm dependencies for visual effects** &mdash; prefer magicui or Tailwind CSS

## Design Philosophy: Interactive > Decorative

This is the single most important lesson from multiple homepage design iterations:

| Approach | User reaction | Example |
|----------|--------------|---------|
| **Dynamic/interactive** | &#x2705; &ldquo;惊艳&rdquo; | Typewriter cycling words, MagicCard mouse-following spotlight, ScrollProgress bar, scroll parallax fade-out |
| **Static visual decoration** | &#x274C; &ldquo;看不出什么内容, 很单调&rdquo; | Emoji anchors, accent bars, gradient backgrounds, noise texture on cards, quick facts bar |

**Priority when asked &ldquo;make it more impressive&rdquo;:**
1. Add dynamic data (GitHub activity, blog posts, live counters) &mdash; content itself becomes the attraction
2. Add interactive feedback (mouse tracking, scroll progress, hover effects with motion) &mdash; page responds to user
3. Add animated motion (typewriter, spring counters, entrance animations with stagger) &mdash; page has rhythm
4. ONLY THEN add static visual polish &mdash; and be conservative

**Key user preferences:**
- Prefers **existing components** (magicui, Aceternity) over custom code
- Interactive > decorative
- Keep visual effects **clean and tasteful** &mdash; avoid gradient text, avoid flashy animations
- Typewriter should **cycle through words** (type &rarr; pause &rarr; delete &rarr; next), not type a static string once
- Research before implementing &mdash; do CSS+JS analysis of reference sites before coding

## 设计偏好

- 标题用纯色 `text-foreground`，不推荐 `AnimatedGradientText`（"有点土"）
- 视觉冲击力通过 subtle animations 实现：粒子背景、打字机效果、hover glow、滚动入场
- 卡片 hover 推荐：`hover:-translate-y-0.5` + `hover:shadow-[0_0_25px_-3px] hover:shadow-primary/15`
- 亮暗模式切换推荐 View Transitions API + clip-path 圆形扩散动画

### 节标题不要用 emoji

所有 section label 的最前方装饰性图标应该使用 lucide-react SVG 图标，而不是 emoji：
- ❌ `📜 Skill Codex` — emoji 在不同平台渲染不一致，且无法控制颜色/大小
- ✅ `<BookOpen className="h-3.5 w-3.5" /> Skill Codex` — SVG 图标精确可控

常用映射：
| Emoji | Lucide Icon | 适用场景 |
|-------|-------------|----------|
| ⚡ | `Zap` | 能力、介绍 |
| 📜 | `BookOpen` | 技能、知识库 |
| 💻 | `Terminal` | 终端、命令行 |
| 🌐 | `Globe` | 联系、社交链接 |

### 所有 section 组件必须加 id 属性

每个 section 组件需要唯一的 `id` 属性，以支持：
- URL fragment 锚点导航（`#hero`, `#codex`）
- SectionNav 等 IntersectionObserver 追踪
- 平滑滚动跳转

```tsx
// 必做
<section id="hero" ref={sectionRef} className="...">
<section id="atlas" ...>
<section id="codex" ...>
<section id="terminal" ...>
<section id="contact" ...>
```

同时在 `globals.css` 的 `html` 上加 `scroll-behavior: smooth`：
```css
html { scroll-behavior: smooth; }
```

### 必须添加 prefers-reduced-motion 支持

在 `globals.css` 中添加媒体查询，尊重用户的减少动画偏好：

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

不添加被认为是无障碍违规。不要在组件中再用 JS 绕开——CSS 层直接归零所有动画是最可靠的方式。

## Pitfalls

1. **不要在 WSL /mnt/ 目录下运行 npm install** — 会因 EPERM 失败。始终在 WSL 原生文件系统（`~/projects/`）下操作。
2. **Tailwind CSS v4 的 @theme inline 语法不同** — 颜色变量需用 `--color-xxx: var(--xxx)` 注册。
3. **shadcn 和 magicui 组件用相同的 CLI 工具** — magicui 组件通过 `npx shadcn@latest add @magicui/<name>` 安装。
4. **CSS 中的 `[&>*]` 等选择器在 Tailwind v4 中需使用 `[&>*]:` 前缀语法**。
5. **Static Export 的 Next.js 项目** — `next.config.ts` 需配置 `output: "export"` 和 `images: { unoptimized: true }`。
6. **View Transitions API 只在 Chrome/Edge/Safari 支持** — Firefox 不兼容，需要 fallback。
7. **TypingAnimation 的 startOnView 默认为 true** — 如果要在 Hero 区立即开始打字，需设为 `false`。
8. **BentoCard 的 `background` prop 是 required** — 如果只是展示简单卡片，直接用 `BentoGrid` 做容器 + 自定义 card content，不要用 `BentoCard`。
9. **BentoGrid 默认 row height 是 `auto-rows-[22rem]`** — 如果需要按内容撑开，覆盖为 `auto-rows-auto`。
11. **`animate-gradient` keyframe 由 magicui CLI 自动添加到 `@theme inline`** — 不需要手动配置。
12. **Framer Motion `ease` 数组在 TypeScript strict 下需要 `as const`** — `ease: [0.25, 0.1, 0.25, 1]` 会被 TS 推断为 `number[]`，framer-motion 要求 `Easing` (tuple)。修复：`ease: [0.25, 0.1, 0.25, 1] as const`。
13. **`useRef<HTMLElement>` 不能绑到 `<div>` 上** — `HTMLElement` 缺少 `align` 等属性，报错 `Type 'RefObject<HTMLElement>' is not assignable to 'Ref<HTMLDivElement>'`。修复：`useRef<HTMLDivElement>(null)`（或具体元素类型）。
14. **SectionNav 等浮动组件在 Server Component layout.tsx 中可能不挂载** — 如果控制台无错误但组件不渲染，在组件顶部加 `console.log("[Component] mounted")` 验证是否到达浏览器。可能原因：HMR 缓存、Client-Server 边界深度嵌套导致 hydrate 跳过。
15. **横向溢出修复用 `overflow-x: clip` 而非 `overflow-x: hidden`** — `hidden` 会破坏 `position: sticky` 和 `position: fixed` 元素的行为，因为它将元素建立为新的滚动容器。`clip` 只裁剪内容不改变滚动行为。在 `html` 和 `body` 上同时设置：
    ```css
    html, body { overflow-x: clip; }
    ```
  16. **Scroll parallax + 内部 mount 动画并存时** — 外层 `motion.div` 用 `style={{ opacity: contentOpacity }}`（MotionValue），内部子元素用 `initial/animate`。framer-motion 正确组合两者：mount 动画运行一次后，MotionValue 接管。不需要特殊处理。

  18. **GitHub Pages 子目录部署必须加 basePath** — Next.js 静态导出生成的资源路径是绝对路径 `/_next/static/...`。如果部署到 `https://user.github.io/repo-name/`（子目录），所有 CSS/JS 会 404，页面看起来是空白的。修复：在 `next.config.ts` 中设置 `basePath: "/repo-name"`，所有路径自动变更为 `/repo-name/_next/static/...`。
    ```ts
    const nextConfig: NextConfig = {
      output: "export",
      basePath: "/hermetic-atlas",  // 必须匹配 GitHub repo 名
      images: { unoptimized: true },
    };
    ```
    验证方法：构建后检查 `out/index.html` 中的 `href` 和 `src` 路径是否都带有正确的前缀。
    `grep -o 'href="[^"]*"' out/index.html | head -5`

  19. **Tailwind v4 无 `bg-gradient-radial` 工具类** — 不要使用 `bg-gradient-radial from-amber-500/5 ...` 这种 Tailwind v3 语法。Tailwind v4 不支持 `bg-gradient-radial`。要用径向渐变，使用任意值语法：
    ```tsx
    <div className="bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-amber-500/5 via-transparent to-transparent" />
    ```
    或者直接 inline style：`<div style={{ background: "radial-gradient(ellipse at center, rgba(217,119,6,0.05), transparent)" }} />`。
    如果用了无效的 Tailwind 类，它只是被静默忽略——页面不会报错但效果也没有。

17. **优先使用高质量/专业级 skill** — 当同时存在多个可用的 skill 时，优先选择更专业、更完整的：
    - `ui-ux-pro-max`（161 配色 + 57 字体 + 99 UX 指南）优先于 `homepage-design` 的简单卡片模式
    - `comet`（OpenSpec + Superpowers 双星工作流）优先于盲写代码
    - `baoyu-infographic`（21 布局 × 21 风格）优先于手写信息图
    - 如果你不确定哪个 skill 更好，先 `skills_list` 查看所有候选，再 `skill_view` 加载比较，不要假设名气最大的就是对的
    - 用户明确说了"不能用劣质技能"——拿出最强的工具

  20. **AnimatePresence 过滤网格用 `mode="sync"` 避免跳跃** — 带分类过滤功能的卡片网格，`mode="popLayout"` 会导致退出元素从布局流移除时网格突然跳跃重排。使用 `mode="sync"`（元素动画完成后再从 DOM 移除），并将过渡时间缩到 `0.2s`：
    ```tsx
    <AnimatePresence mode="sync">
      {filteredItems.map(item => (
        <motion.div key={item.id} layout
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          transition={{ duration: 0.2 }}
        >...</motion.div>
      ))}
    </AnimatePresence>
    ```

  21. **TypingAnimation 在 Hero 标题中加速** — 默认 `duration={100}` 对 12+ 字符长的标题（如 "The Hermetic Atlas"）太慢，用户会看到光标卡在文字中间。Hero 区核心标题设置 `duration={20}` 让打字在 1-2 秒内完成。测试标准：用户不应该能在视觉上"等待"打字完成。
