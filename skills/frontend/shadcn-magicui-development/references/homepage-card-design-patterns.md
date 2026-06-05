# Homepage Card Design Patterns

> Absorbed from `homepage-design` skill (archived). Class-level card patterns for Next.js + shadcn/ui homepages.

## Accent Bar (Top Edge)

Two variants — depends on whether you need absolute positioning:

**Variant A — Absolute (no structural impact):**
```tsx
<div className="relative flex flex-col rounded-2xl border bg-card overflow-hidden">
  <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-primary to-primary/60" />
  <div className="p-6 pt-7">...</div>
</div>
```

**Variant B — Structural (simpler, no pt adjustment):**
```tsx
<div className="relative flex flex-col rounded-2xl border bg-card overflow-hidden">
  <div className="h-[3px] w-full shrink-0 bg-gradient-to-r from-primary/40 to-primary/10" />
  <div className="p-6">...</div>
</div>
```

## Emoji Visual Anchor (Use sparingly — interactive effects preferred)

Place a large emoji (32-40px) near the top-left of each card:
```tsx
<span className="text-3xl leading-none mb-3 block">🌏</span>
```

## Subtle Gradient Background (Hero card only)

Instead of flat `bg-card`, use a subtle directional gradient:
```tsx
className="bg-gradient-to-br from-card via-card to-primary/[0.03]"
```

Apply ONLY to the hero card in a bento grid for visual hierarchy.

## Left Accent Strip (Blog/article cards)

For list-style card sections, replace flat cards with a colored left vertical strip:
```tsx
<Card className="rounded-2xl border-border/60 overflow-hidden">
  <CardContent className="p-0 flex">
    <div className="w-[4px] shrink-0 bg-gradient-to-b from-purple-500/60 to-purple-400/30" />
    <div className="flex items-center justify-between flex-1 min-w-0 p-5 pl-4">
      ...content...
    </div>
  </CardContent>
</Card>
```

## Flex Column with Sticky Footer

When card content has variable height, use flex to push tags to the bottom:
```tsx
<div className="p-6 flex flex-col h-full">
  <p className="text-sm flex-1">{desc}</p>
  <div className="flex flex-wrap gap-2 mt-auto pt-3">
    <Badge variant="secondary">标签</Badge>
  </div>
</div>
```

## Quick Facts Bar (About section)

```tsx
<div className="flex flex-wrap gap-3 text-xs text-muted-foreground mt-4 pt-4 border-t border-border/40">
  <span>🎂 19岁</span>
  <span>📍 中国</span>
  <span>📝 20+篇</span>
</div>
```

## Hover Trifecta (Combined effect)

```tsx
className="transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_0_25px_-3px] hover:shadow-primary/20 hover:border-primary/30"
```

## What to AVOID

- **Static decoration without interactive effects** — The user consistently rejects decorative-only changes (accent bars, emoji anchors, gradient backgrounds, noise texture on cards) as "看不出内容" and "单调". Always lead with interactive effects (MagicCard, ScrollProgress, OrbitingCircles) before proposing any static visual polish.
- **Aceternity 3D Card** — `CardBody` hardcodes `h-96 w-96`, breaks Bento Grid layouts. Use MagicCard or simple CSS hover instead.
- **Nesting ShineBorder inside MagicCard** — The two components fight over z-index layers. Pick one effect per card.
- **Animated gradient borders** — Requires `@property` CSS which has Firefox compatibility gaps.
- **New npm dependencies for visual effects** — Always prefer magicui components or pure Tailwind CSS.

## Project State Management (AGENTS.md)

Maintain a **living AGENTS.md** at the project root for cross-session resumption:

**What it should contain:**
- Current section-by-section status table (✅ done / ⏳ pending)
- All design decisions and user preferences (font choices, animation preferences, color rules)
- Pending roadmap items
- Relevant Hermes skill references (linked to `skill_view`)
- Deployment info and commands

**Convention:**
- Update AGENTS.md after every meaningful batch of changes
- Keep the "Pending / Roadmap" section as the canonical next-step list
- List relevant skills under "Relevant Skills" so the agent knows what to load

**Why:** AGENTS.md auto-loads into the agent's system prompt when the project directory is the workdir.
