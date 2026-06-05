# qzq.at — Interactive Effects Analysis

**Site:** https://www.qzq.at/ (SamuelQZQ / 数字游牧人)
**Tech Stack:** Next.js (Pages Router) + Tailwind CSS v3.2.7 + Motion (`motion.dev`) + Font Awesome 6
**No framer-motion, no GSAP** — all interactivity via React hooks + CSS + Motion library

## 1. 3D Tilt Card Effect

**How it works:** Custom React component using `MouseEnterProvider` context + `transform-style: preserve-3d`

```
CardContainer (perspective: 1000px)
  └─ TiltContainer (transform-style: preserve-3d)
       └─ Tilt component (reads mouse position from context)
            └─ Applies CSS transform on mousemove:
               translateX/Y/Z + rotateX/Y/Z (6 DOF)
            └─ Resets to zero on mouseleave
            └─ transition: all 200ms ease-linear
```

**Props:** `as`, `translateX/Y/Z`, `rotateX/Y/Z` — all default to 0

**Key difference from Aceternity:** qzq.at's version is simpler — no CardItem depth separation, just a single tilt on the whole element.

## 2. Animated Follower Counter

**Library:** Motion (`motion.dev`) — specifically `useSpringValue` + `useSpring`

```
AnimatedNumber({ value, direction="up", delay=0 })
  ├─ useSpringValue(0)        ← spring animation target
  ├─ useSpring(springValue, { damping: 60, stiffness: 100 })
  ├─ useInView(ref, { once: true, margin: "0px" })
  ├─ On view: setTimeout → springValue.set(value)
  ├─ On spring change: ref.current.textContent = Intl.NumberFormat("en-US").format(val)
  └─ Renders: <span className="inline-block tabular-nums" ref={ref} />
```

**Follower total calculation:**
```js
total = bilibiliMain.followers + bilibiliGame.followers + twitter.followers + tiktok.followers + xiaoHongShu.followers
```

Cards have colored backgrounds: `bg-pink-800`, `bg-indigo-800`, `bg-green-800`, `bg-purple-700`, `bg-blue-800`, `bg-teal-800`

## 3. Infinite Scroll Marquee

**Structure:**
- Container: `scroller relative z-20 overflow-hidden [mask-image:linear-gradient(to_right,transparent,white_20%,white_80%,transparent)]`
- Inner list: `flex min-w-full shrink-0 gap-4 py-4 w-max flex-nowrap animate-scroll`
- On mount: clones all children for seamless loop
- Speed: fast=20s, normal=40s, slow=80s (`--animation-duration`)
- Direction: `--animation-direction` (forwards/reverse)
- `hover:[animation-play-state:paused]`

## 4. Scroll Parallax

Uses Motion's `useScroll` + `useSpring`:
- Tracks scroll position via `useScroll()`
- Maps position to value range
- Applies smooth `y` translation via `useSpring`

## 5. Noise Texture Overlay

Each card has a noise overlay div:
```html
<div class="absolute inset-0 w-full h-full scale-[1.2] transform opacity-10
            [mask-image:radial-gradient(#fff,transparent,75%)]"
     style="background-image: url(/noise.webp); background-size: 30%" />
```

Note: They use a static noise.webp image. Our SVG inline approach (in the main skill) is superior — no extra network request.

## 6. Other CSS Animations

| Effect | CSS |
|--------|-----|
| Location pulse | `@keyframes pulse` with orange box-shadow spreading from 0 to 90px |
| Orbit (decorative circles) | `@keyframes orbit` with `--radius` and `--duration` CSS vars |
| Page fade-in | `@keyframes fade-in-animation` 0.3s ease-in |
| Custom scrollbar | 6px width, track `#d1d5db`, thumb `#334155`, hover `#fb923c` (orange) |

## 7. Card Structure

Each social card is an `<li>` with:
```
rounded-2xl border border-b-0 border-slate-700 px-8 py-6 overflow-hidden
flex flex-col gap-1
w-[350px] max-w-full md:w-[450px]
bg-{color}-800
```

Content: name + platform badge + stats (followers/views/videos) + quote
Cards cycle colors: pink-800, indigo-800, green-800, purple-700, blue-800, teal-800

## 8. Pages

- `/` — Main page with hero, experience, skills, projects, testimonials
- `/favorites` — Chronological list of inspirations by year (2024→2017)
- `/influencer`, `/code`, `/game`, `/music`, `/books` — dedicated section pages

## Key Takeaways

1. No animation framework — pure CSS + React hooks + Motion library
2. The 3D tilt is the most impactful feature with minimal code
3. Noise texture adds premium feel (even at very low opacity)
4. Animated counters feel alive without being distracting (spring physics, not setInterval)
5. The site's personality comes from content structure (Favorites timeline) more than visual effects
