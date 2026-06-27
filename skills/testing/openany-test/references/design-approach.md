# Design Approach: Tool-Grade vs Consumer Landing

## The mistake (Phase 5a original)

Initial design applied consumer-landing patterns to a developer tool:
- `BorderBeam` with indigo→cyan conic gradient
- Floating particles / radial glow background
- Decorative `backdrop-blur-md` on toolbar
- Blue-purple button accents (`bg-indigo-600`, `shadow-indigo-500/20`)

User response: "典中典蓝紫色AI味渐变" — this violates the LILA RULE from `design-taste-frontend`.

## The fix (Phase 5b redesign)

Applied `design-taste-frontend` framework properly:
1. **Design Read**: "desktop file viewer tool for developers, VS Code / Linear tool-grade aesthetic"
2. **Dials**: MOTION_INTENSITY 3-4, VISUAL_DENSITY 5-6, DESIGN_VARIANCE 4-5
3. **Palette**: zinc-neutral base, no gradient accents, single accent color
4. **Motion**: only functional transitions (tab open/close, content switch) — no decorative loops
5. **Added**: StatusBar with file count, encoding, format info (tool-grade information density)

## Concrete anti-patterns for this project

| ❌ Don't | ✅ Do |
|---|---|
| `from-indigo-500 to-cyan-400` gradient | `bg-zinc-700 hover:bg-zinc-600` |
| `shadow-indigo-500/20` glow | `border-border` subtle border |
| `BorderBeam` rotating beam | Clean border, no decoration |
| `backdrop-blur-md` on everything | `bg-surface/80 backdrop-blur-sm` where useful |
| Particles / radial glow backgrounds | Subtle `.bg-dot-pattern` (6% opacity) |
| `scale: 1.1` button hover | `scale: 1.03` subtle hover |

## When to use decorative effects

Only when ALL of:
1. The design read explicitly calls for it (e.g. landing page, not tool)
2. The user has approved the direction
3. The effect communicates real hierarchy, not just "looks cool"

For this project, these conditions are never met.
