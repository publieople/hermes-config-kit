# Dark-Tech CRT Design Patterns

Proven implementation patterns for dark-tech / retro-terminal aesthetic.
Created during Publieople homepage redesign — CRT scanlines, dot-grid backgrounds,
glow-pulse typography, and neon-conic-gradient card borders.

---

## CRT Scanline Overlay

Subtle repeating horizontal lines with edge vignette and optional flicker.
Place as fixed full-screen overlay with `pointer-events-none` + high z-index.

```css
/* Scanlines: repeating transparent gaps create the line effect */
background-image: repeating-linear-gradient(
  0deg, transparent, transparent 3px,
  rgba(0,0,0,0.03) 3px, rgba(0,0,0,0.03) 4px
);

/* Screen edge vignette */
background: radial-gradient(ellipse at center, transparent 60%, rgba(0,0,0,0.15) 100%);
```

```css
@keyframes crt-flicker {
  0%, 100% { opacity: 0; }
  50% { opacity: 0.03; }
}
```

Key: spacing=3-4px, opacity=0.03-0.06. Always `pointer-events-none` + `aria-hidden="true"`.

---

## Dot Grid Background

Radial-gradient dots at regular intervals, faded at edges via mask-image.

```css
background-image: radial-gradient(circle, var(--primary) 0.5px, transparent 0.5px);
background-size: 28px 28px;
mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 40%, transparent 100%);
```

Spacing: 24-40px. The mask is critical — without it reads as a pattern fill.

---

## Title Glow Pulse

Layered text-shadow with CSS animation for breathing neon effect.

```css
@keyframes glow-pulse {
  0%, 100% {
    text-shadow: 0 0 20px var(--primary), 0 0 40px var(--primary), 0 0 80px var(--primary);
  }
  50% {
    text-shadow: 0 0 10px var(--primary), 0 0 20px var(--primary), 0 0 40px var(--primary);
  }
}
```

Duration: 3s, easing: ease-in-out. Three shadow layers for depth.

---

## Neon Conic-Gradient Card Border

Rotating conic-gradient border on hover. Blurred glow (behind) + sharp ring (on top).

```css
/* Glow layer behind card */
background: conic-gradient(
  from 0deg, var(--primary), transparent 40%, transparent 60%, var(--primary), transparent
);
animation: neon-spin 4s linear infinite;
filter: blur(4px);
```

```css
@keyframes neon-spin { to { transform: rotate(360deg); } }
```

Stops at 40%/60% create a "beam" effect. Apply via `group-hover`:
`opacity-0 group-hover:opacity-100 transition-opacity duration-500`

Wrapper needs `position: relative`; glow rings use `position: absolute -inset-[1px]`.

---

## Pitfalls

- CRT scanlines > 0.08 opacity = broken monitor look
- Dot grid without mask = tablecloth pattern
- Glow pulse on dark bg: increase spread or add bg radial glow behind element
- Conic-gradient: animate `transform: rotate()` (GPU-composited), NOT background-position
- Flicker at 0.15s is intentionally fast — slower = distracting blink
- All patterns behind `pointer-events-none`; use `prefers-reduced-motion` fallback
