# Migration Analysis — Greenfield Rebuild Planning

Use when the user wants to **rebuild an existing codebase with a new tech stack** while preserving the original design/behavior. Combines Mode A (Implementation Plan) and Mode B (Comparative Analysis) from the parent plan skill.

## Trigger phrases

"用现代技术栈重构" / "改用 X 替代 Y" / "迁移到 Z" / "rebuild this with modern stack" / "重写" when a working codebase already exists.

## Process

### 1. Inventory current state

Before proposing anything, read the actual codebase:

- **File tree**: `find /path -type f -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.html" -o -name "*.css" -o -name "*.json"` sorted
- **Line counts**: rough total per major file (head/tail or wc)
- **Dependencies**: pyproject.toml / package.json / requirements.txt / Cargo.toml
- **Pages/routes**: every HTML template or route handler
- **Design system**: CSS variables, theme tokens, component classes — this is the most-copied part in a design-preserving rebuild
- **Critical algorithms**: anything that shouldn't change (protocol parsers, signal processing, game physics)
- **README / AGENTS.md / docs**: to understand the project's own mental model

Document all of this in the plan. The user will verify it against their own knowledge.

### 2. Map: Keep vs Rewrite

| Category | Handle | Example |
|----------|--------|---------|
| **Algorithm code** | Copy as-is, adapt imports | TGAM protocol parser, EEG FFT, fusion engine |
| **Design system** | Re-theme to new framework | CSS variables → Tailwind tokens |
| **UI pages** | Rewrite with new framework | HTML templates → React/Vue components |
| **Game/render logic** | Translate module-by-module | JS Canvas → TypeScript Canvas |
| **Backend logic** | Restructure into modules | Monolithic main.py → package structure |
| **Third-party libs** | Upgrade or keep | jQuery → modern equivalent or remove |

### 3. Choose modern stack

Produce a comparison table for the key choices:

| Layer | Current | Candidate | Rationale |
|-------|---------|-----------|-----------|
| Frontend framework | Vanilla HTML/JS | Vite + React SPA | Familiar, fast builds, type-safe |
| Language | JS | TypeScript strict | Type safety across the stack |
| Styling | Custom CSS | Tailwind v4 + tokens | Maintainable, preserves design |
| Backend | FastAPI (mono) | FastAPI (modular) | Keep; just reorganize |
| Database | PostgreSQL | SQLite (dev) / PG (prod) | Environment-switchable |

Include "why NOT" notes for rejected options (e.g. "Next.js is overkill for a Canvas game — SPA is simpler").

### 4. Design-verification table

Show exactly how each visual element maps:

| Original | New | Fidelity |
|----------|-----|----------|
| `.glass-panel` with CSS variables | `<GlassPanel>` React component | 100% |
| `.btn-primary` gradient | `<Button variant="primary">` | 100% |
| Dynamic fluid background | `<FluidBg>` with same CSS keyframes | 100% |
| Game Canvas rendering | Same Canvas API, TS class | ~90% (API preserved, structure improved) |

### 5. Phased implementation plan

Break into phases ordered by dependency. Typical pattern:

- **Phase 0**: Scaffold (repo, project init, Comet artifacts, CI)
- **Phase 1**: Core backend (modules, ORM, WebSocket manager)
- **Phase 2**: Design system migration (tokens, component library, routing)
- **Phase 3-N**: Each page/game module, one per phase
- **Phase N+1**: Integration (WebSocket, device drivers, testing)
- **Phase N+2**: Deployment (build pipeline, Docker, CI/CD)

Each phase should be independently verifiable (e.g. "Phase 2 done = components render correctly in Storybook or dev server").

### 6. Risk assessment

| Risk | Mitigation |
|------|-----------|
| Canvas game engine rewrite is large | Ship core loop first; add enemy systems iteratively |
| Design fidelity in new framework | Keep CSS keyframe animations; use inline styles where Tailwind can't express |
| External dependencies have compatibility issues | Pin versions; use legacy-peer-deps or install-strategy=nested |
| Comet/OpenSpec tooling not installed | Use manual artifact creation (greenfield bootstrap path) |
