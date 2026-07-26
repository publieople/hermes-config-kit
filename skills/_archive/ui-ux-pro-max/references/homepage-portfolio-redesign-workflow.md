# Portfolio / Homepage Redesign Workflow

A proven workflow for using ui-ux-pro-max to redesign a personal homepage or portfolio site.

## Context

Used for: Publieople's Homepage (www.for-people.cn), Next.js + Tailwind v4 + shadcn/ui + magicui + framer-motion

## Multi-Step Search Strategy

### Step 1: Generate Full Design System
```bash
python3 scripts/search.py "<product_type> <industry> <keywords>" --design-system -p "Project Name" -f markdown
```
**Query strategy:** Combine product type + audience + tone. E.g. `"personal portfolio homepage brand identity creative professional"`

Returns: Pattern, Style, Colors (with hex tokens), Typography (with Google Fonts import), Key Effects, Anti-patterns, Pre-delivery checklist.

### Step 2: Landing Page Patterns
```bash
python3 scripts/search.py "portfolio personal brand content creator landing" --domain landing -n 3
```
Get section order recommendations and CTA placement strategies for the specific use case.

### Step 3: Style Deep-Dive
```bash
python3 scripts/search.py "modern creative portfolio interaction animation scroll" --domain style -n 5
```
Browse multiple style options with performance/accessibility ratings and implementation checklists. Cross-reference with the design system recommendation.

### Step 4: Color Palette Specific
```bash
python3 scripts/search.py "personal brand portfolio creative" --domain color -n 3
```
Get alternative color systems with full token sets (hex + CSS variable names). Compare with existing theme.

### Step 5: UX Best Practices
```bash
python3 scripts/search.py "portfolio personal homepage scroll navigation section" --domain ux -n 4
```
Check navigation, responsive, and accessibility rules specific to the landing type.

## Synthesis into Proposal

Combine all results into a structured proposal covering:

1. **Current diagnosis** — table of each section × (status + problem)
2. **Design system** — chosen style, typography, color rationale
3. **Per-section redesign** — for each section: what to keep, what to change, what effect to add
4. **New global effects** — ranked by impact
5. **Priority roadmap** — P0/P1/P2 with time estimates

## Implementation Patterns

After the design system is approved, the following implementation patterns apply (Next.js + framer-motion + magicui context):

### Section Transition Differentiation
Don't use the same `whileInView` animation for every section. Vary entry direction per section to create visual rhythm:
- **About / Resume** → fade up (`y: 40`)
- **Projects** → fade from left (`x: -30`)
- **Blog** → fade from right (`x: 30`)
- **Contact** → scale in (`scale: 0.95`)

**TypeScript gotcha:** framer-motion ease arrays must use `as const` to satisfy type checking:
```tsx
transition: { duration: 0.6, ease: [0.25, 0.1, 0.25, 1] as const }
```
Without `as const`, TypeScript infers `number[]` instead of the expected tuple `[number, number, number, number]`.

### Emoji → Lucide Replacement Pattern
Replacing structural emoji with Lucide icons:
1. Import from `lucide-react` (already a dependency)
2. Wrap in a styled container `inline-flex size-10 items-center justify-center rounded-xl bg-primary/10`
3. Remove emoji from data and replace with icon component references
4. Keep inline emoji only if the brand itself uses them (Notion, Slack, early Linear)

### Number Counter Animation on Scroll
Simple `useState` + `setInterval` approach with `useInView` trigger:
```tsx
const [count, setCount] = useState(0);
const ref = useRef(null);
const isInView = useInView(ref, { once: true, margin: "-40px" });

useEffect(() => {
  if (!isInView) return;
  let start = 0;
  const step = Math.max(1, Math.ceil(to / (1000 / 16)));
  const timer = setInterval(() => {
    start += step;
    setCount(start >= to ? to : start);
    if (start >= to) clearInterval(timer);
  }, 16);
  return () => clearInterval(timer);
}, [isInView, to]);
```

### 3D Tilt Card
Mouse-follow 3D rotation using `onMouseMove`:
```tsx
const handleMouseMove = (e) => {
  const rect = cardRef.current.getBoundingClientRect();
  const x = e.clientX - rect.left, y = e.clientY - rect.top;
  const rotateX = ((y - rect.height / 2) / (rect.height / 2)) * -8;
  const rotateY = ((x - rect.width / 2) / (rect.width / 2)) * 8;
  cardRef.current.style.transform = `perspective(400px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
};
```
Key: `transformStyle: "preserve-3d"` on the container, and `transition: "transform 0.4s ease-out"` on mouse leave for smooth return.

### Blog Horizontal Scroll-Snap
For content sections that need a "showcase" feel:
```html
<div class="flex gap-4 overflow-x-auto snap-x snap-mandatory [scrollbar-width:none]">
  <div class="shrink-0 w-[280px] sm:w-[320px] snap-start">
    <!-- card content -->
  </div>
</div>
```
Each card has a gradient header area, content area that pushes up on hover, reading time progress bar (decorative), and external link indicator.

### Right-Side Section Navigation Indicator
Fixed `<nav>` on the right edge with dots for each section:
- Use native `<a href="#id">` for guaranteed scroll-to behavior (works without JavaScript)
- Hover reveals tooltip label on the left
- Vertical gradient line as connector
- On desktop only: `hidden md:flex`
- Active state tracking requires client JS (IntersectionObserver or scroll listener with `requestAnimationFrame`)

## Known Pitfalls

- **Script path:** The registered skill's `linked_files` may point to `.claude/skills/<skill-name>/scripts/` but the actual runnable scripts might be in `src/<skill-name>/scripts/`. Always check both. Use `find ~/.hermes/skills/openclaw-imports/<repo> -name "search.py"` to locate.
- **Design system output dominates:** The `--design-system` flag is good for broad direction, but always supplement with `--domain` searches for specific dimensions (style variants, UX rules, landing patterns).
- **User design preferences override:** The tool's color recommendations (e.g., monochrome+blue for portfolio) may conflict with existing brand colors. Use as inspiration, not prescription. Cross-check with user's stated preferences (dislikes gradient titles, values motion effects over static decoration).
- **Next.js hydration vs browser testing:** When testing locally via `npm run dev`, the browser tools snapshot may show the SSR'd static state rather than the hydrated client state. Effects that rely on `useEffect` / `useState` (like counter animations, active nav tracking) won't show in the snapshot. Always check the browser console for errors first.
- **SectionNav placement matters:** Placing a client component with DOM manipulation (`useEffect`) inside a server component layout (`layout.tsx`) can prevent hydration. If the component doesn't render, move it to a client page component (`page.tsx` with `"use client"`) instead.
