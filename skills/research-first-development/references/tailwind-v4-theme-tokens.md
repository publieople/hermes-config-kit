# Tailwind v4 Design Tokens for Dark/Light Mode

## The Pattern (Zero libraries, native TW v4)

```css
@import "tailwindcss";
@custom-variant dark (&:where(.dark, .dark *));

@theme {
  --color-surface: #1e1e1e;
  --color-surface-alt: #252526;
  --color-border: #374151;
  --color-text: #d1d5db;
  --color-text-muted: #9ca3af;
}

.dark {
  --color-surface: #f8fafc;
  --color-surface-alt: #e2e8f0;
  --color-border: #cbd5e1;
  --color-text: #334155;
  --color-text-muted: #475569;
}
```

Then use `bg-surface`, `text-text-muted`, `border-border` in components. No per-element `dark:` variants needed.

## Anti-Patterns

### ❌ Hardcoded hex (can't be themed)
```tsx
className="bg-[#1e1e1e] border-gray-700 text-gray-400"
```

### ❌ Verbose `dark:` per element
```tsx
className="bg-slate-900 dark:bg-slate-100 border-slate-700 dark:border-slate-300"
```
Works, but bloats every className. Hard to change colors later.

### ✅ Semantic tokens
```tsx
className="bg-surface border-border text-text-muted"
```
Single source of truth. Change colors in CSS, all components follow.

## Why This Over `next-themes` or Other Libraries

- `next-themes` is Next.js-specific. Not applicable to Vite SPA.
- No JS library needed — TW v4 `@theme` is native, 0 KB runtime.
- The `<html class="dark">` toggle + Zustand store for state is 10 lines.
