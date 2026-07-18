# Ghost Card Design References — Design Analysis

Two reference images were analyzed in session 2026-05-16 for the Ghost Card (悬浮透明卡片) hackathon project.

## Reference 1: Rainy Night AR Ghost Card (screenshot1.png)

**Context:** A Douyin-like video feed showing a rainy night street corner with a convenience store.

### Visual Breakdown

- **Ghost mascot**: A glowing, semi-transparent ghost character sitting in a puddle on the road. Emits warm yellow light matching the convenience store glow. Functions as AI assistant / mascot.
- **Card content**: Two lines — "Rain stops in 47 minutes" / "Late-night cafe still open nearby"
- **Card position**: Next to the ghost, floating in 3D space (not pinned to screen edges)
- **Card style**: Glassmorphism — no solid background, extremely light semi-transparent layer, thin 1px white border, backdrop blur

### Design Language

- Immersive: UI elements transparent enough not to interrupt video viewing
- Emotional: Creates a "cozy companion" vibe through rain, warm lights, and a cute ghost
- Diegetic UI: The card feels like it belongs in the video scene, not on top of it

## Reference 2: Moganshan Memory Card (screenshot2.png)

**Context:** A moody mountain road at dusk, Moganshan, China. Cafe with "OPEN" neon sign on the right.

### Visual Breakdown

- **Header**: Three items — "AI MEMORY" tag, "NO.097", "2025.06.01"
- **Title**: Large serif font — "The mountains are getting quieter tonight"
- **Body**: "You've been seeking stillness, nature, and slower moments. Moganshan responds in silence."
- **Data list**: 4 rows with icons — Fog Density (increasing), Nearby Cafe (open 21:30), Night Run (16° humid), Ambient Sound (tap to listen)
- **Footer**: Location (Moganshan, China + GPS) + "Refreshed by your mood and recent interests"
- **Map integration**: "YOU ARE HERE" marker on the road in the background photo

### Design Language

- Dark mode aesthetic
- Glassmorphism card with low-opacity white background + backdrop blur
- Road texture visible through the card
- Generous whitespace inside card
- Content organized in clear zones: header → narrative → functional data
- Diegetic UI: "YOU ARE HERE" marker bridges card and background scene

## Recurring Glassmorphism Properties

```
background: rgba(255, 255, 255, 0.05–0.08);
backdrop-filter: blur(20px);
border: 1px solid rgba(255, 255, 255, 0.2);
border-radius: 12–16px;
```

## When to Use Each Style

| Scenario | Style | Example |
|----------|-------|---------|
| Quick contextual tip | Style A (minimal) | "Rain stops in 47 min" |
| Rich content recommendation | Style B (structured) | Moganshan memory card |
| Commercial card with CTA | Hybrid | F1 ticket with "AI推荐" tag |
| Emotional/storytelling content | Style B | "The mountains are getting quieter" |
