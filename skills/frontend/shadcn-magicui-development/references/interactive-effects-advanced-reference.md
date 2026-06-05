# Advanced Interactive Effects Reference

> Absorbed from `shadcn-homepage-effects` skill (archived). Complementary deep-dive for interactive effects on shadcn/ui + magicui homepages. Covers components not detailed in the main SKILL.md, plus critical positioning details.

## MagicCard (Mouse-following Spotlight)

**Install:** `npx shadcn@latest add https://magicui.design/r/magic-card`

The best "wow" effect for individual cards. A spotlight/gradient follows cursor position with spring physics.

### Gradient Mode (default)
```tsx
<MagicCard
  className="rounded-2xl cursor-pointer h-full"
  gradientColor="#262626"
  gradientFrom="#9E7AFF"
  gradientTo="#FE8BBB"
>
  <YourCard />
</MagicCard>
```

### Orb Mode (more dramatic — hero/featured cards)
```tsx
<MagicCard
  mode="orb"
  className="rounded-2xl cursor-pointer h-full"
  glowFrom="#ee4f27"
  glowTo="#6b21ef"
  glowSize={420}
  glowBlur={60}
  glowOpacity={0.9}
>
  <YourCard />
</MagicCard>
```

### How it works internally
- Tracks `pointermove` events on wrapper, stores x/y in `motion.value`
- Gradient mode: `useMotionTemplate` renders a `radial-gradient` at cursor position as `background`
- Inner `absolute inset-px z-20 bg-background` div provides card background surface
- Inner `z-30` div with `opacity-0 group-hover:opacity-100` shows spotlight on hover only
- Content goes in `z-40`
- `group` class is on MagicCard — `group-hover:` works on children

### MagicCard Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `className` | string | — | Container class. SET `rounded-2xl` here |
| `mode` | `"gradient"` | `"orb"` | Effect type |
| `gradientColor` | string | `"#262626"` | Spotlight color (gradient mode) |
| `gradientOpacity` | number | `0.8` | Spotlight opacity |
| `gradientFrom` | string | `"#9E7AFF"` | Border gradient start |
| `gradientTo` | string | `"#FE8BBB"` | Border gradient end |
| `gradientSize` | number | `200` | Spot radius in px |
| `glowFrom` | string | `"#ee4f27"` | Orb color start |
| `glowTo` | string | `"#6b21ef"` | Orb color end |
| `glowSize` | number | `420` | Orb diameter in px |
| `glowBlur` | number | `60` | Orb blur in px |
| `glowOpacity` | number | `0.9` | Max orb opacity |

### Pitfalls
- MagicCard uses `rounded-[inherit]` — it inherits `border-radius` from its parent or own `className`. Always set `rounded-2xl`.
- MagicCard has `border border-transparent` — visible border comes from gradient background.
- Removes need for `bg-card`, `border-border`, and hover-effect classes on the card itself.
- **Do NOT nest ShineBorder inside MagicCard** — z-index and border-radius conflicts.

## ShineBorder (Animated Gradient Border)

**Install:** `npx shadcn@latest add https://magicui.design/r/shine-border`

An animated gradient border that rotates around the card's perimeter. Best used on ONE card as visual anchor.

```tsx
<div className="relative overflow-hidden rounded-2xl">
  <ShineBorder
    shineColor={["#A07CFE", "#FE8FB5", "#FFBE7B"]}
    duration={10}
    borderWidth={1}
  />
  <div className="p-6">...</div>
</div>
```

### Pitfalls
- Requires `animate-shine` keyframe in globals.css (added automatically by CLI)
- Use with `overflow-hidden` on parent to prevent edge bleeding
- **CRITICAL: Do NOT nest ShineBorder inside MagicCard** — z-index and border-radius conflicts

## Scroll Progress Bar

**Install:** `npx shadcn@latest add https://magicui.design/r/scroll-progress`

Shows a thin gradient bar at the top of the page that fills as the user scrolls.

```tsx
// In layout.tsx
import { ScrollProgress } from "@/components/ui/scroll-progress";

<body>
  <ThemeProvider>
    <ScrollProgress className="top-[65px]" />
    {children}
  </ThemeProvider>
</body>
```

Default gradient is purple-to-pink. Override via `className`. Simplest component in magicui — zero config.

## OrbitingCircles Positioning Deep-Dive

**Install:** `npx shadcn@latest add https://magicui.design/r/orbiting-circles`

### The Two-Bug Positioning Fix

**Bug 1 — `inline-block` baseline gap:** `inline-block` containers reserve space for text baselines, making them taller than their content. `top: 50%` of this taller container ≠ avatar center.

❌ **WRONG** — parent `relative inline-block`:
```tsx
<div className="relative inline-block">   {/* 96×103 NOT 96×96! */}
```

✅ **CORRECT** — explicit `size-24 flex items-center justify-center mx-auto`:
```tsx
<div className="relative size-24 flex items-center justify-center mx-auto">
  {/* exactly 96×96, same as Avatar */}
```

**Bug 2 — `transform-origin: 50% 50%` offset:** Each orbit icon's CSS animation applies `rotate() translateY(radius) rotate()` from the icon's own center. Since `left: 0; top: 0` puts the icon's top-left at the anchor point, the rotation center is offset by `(iconSize/2, iconSize/2)`.

✅ **CORRECT** — offset by `iconSize/2`:
```tsx
<div className="absolute pointer-events-none"
     style={{ left: 'calc(50% - 16px)', top: 'calc(50% - 16px)' }}>
```

### Planetary Ring (3D tilt effect)

The `ring` prop tilts the orbit plane so the circular path looks elliptical:

```tsx
<OrbitingCircles radius={140} iconSize={32} ring ringAngle={60}>
```

**CSS 3D chain (how it works):**
```
[w-0-h-0: rotateX(ringAngle), preserve-3d]  ← tilt orbit plane
  [orbit-item: animation, preserve-3d]       ← orbital motion in tilted plane
    [counter-wrapper: rotateX(-ringAngle), preserve-3d]  ← counter-tilt icon back
      [icon] ← face-on
```

Three things MUST be true:
1. w-0-h-0 container: `transform: rotateX(ringAngle); transform-style: preserve-3d`
2. Orbit animation div: `transform-style: preserve-3d` inline
3. Counter-rotate wrapper: CHILD of animation div (not parent)

### Icon sourcing for orbits

| Tier | What | Source | 
|------|------|--------|
| Brand icons (inner orbit) | Specific product logos | `@lobehub/icons` (npm install) |
| Generic icons (outer orbit) | Conceptual representations | `lucide-react` (already installed) |

### Icon name readability rule (Publieople)

Prefer visually intuitive names:
| ✅ Good | ❌ Avoid |
|---------|----------|
| Terminal, Globe, BookOpen, Zap, Wand2, Rocket, Bot | Code2, Feather, Sparkles, Hash, Palette |

## Design Philosophy: Interactive vs Decorative

This is the single most important lesson from multiple design iterations:

| Approach | User reaction | Example |
|----------|--------------|---------|
| **Dynamic/interactive** | ✅ "惊艳" | Typewriter, MagicCard, ScrollProgress, scroll parallax |
| **Static visual decoration** | ❌ "看不出什么内容, 很单调" | Emoji anchors, accent bars, gradient backgrounds, noise texture |

**Priority when asked "make it more impressive":**
1. Add dynamic data (GitHub activity, blog posts) — content itself becomes attraction
2. Add interactive feedback (mouse tracking, scroll progress, hover effects) — page responds
3. Add animated motion (typewriter, spring counters, entrance animations) — page has rhythm
4. ONLY THEN add static visual polish — and be conservative

## Key User Preferences (Publieople)

- Prefers **existing components** over custom code
- **Interactive > decorative**
- Keep visual effects **clean and tasteful**
- Typewriter should **cycle through words**, not type a static string once
- Research before implementing

## Verification Checklist

- [ ] `npm run build` passes
- [ ] Effects degrade gracefully (no JS errors)
- [ ] `prefers-reduced-motion: reduce` respected
- [ ] Mobile: tilt effects don't interfere with scrolling
- [ ] Dark mode: effects look correct
