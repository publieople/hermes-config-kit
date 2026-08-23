# React 19 + Vitest + jsdom Testing

## The `React.act is not a function` Problem

React 19's CJS build does not export `act`. Vitest resolves `react` and `react-dom` as CJS by default.
`@testing-library/react`'s `render()` calls `act()` internally, which fails because `react-dom/cjs/react-dom-test-utils`
calls `require('react').act` — undefined in React 19 CJS.

## Solutions

### A. Test Element Construction Instead of DOM Rendering

Call handler `Viewer`/`Editor` functions directly and inspect the JSX element tree.
Does not require `render()` — no act dependency.

```tsx
it('Viewer returns a React element', () => {
  const el = fileHandler.Viewer({ file: makeFile() });
  expect(el).toBeDefined();
  expect(typeof el.type).toBe('function');
  expect(el.props.readOnly).toBe(true);
});

it('renders without crash for various extensions', () => {
  for (const ext of ['py', 'js', 'ts', 'html', 'css']) {
    const file = makeFile({ name: `test.${ext}`, extension: ext });
    const el = textHandler.Viewer({ file });
    expect(typeof el.type).toBe('function');
  }
});
```

Trade-off: Can't test DOM output (screen.getByText, etc.) but validates component structure, prop forwarding, and crash-free rendering.

### B. Polyfill act in vitest.setup.ts

```ts
// vitest.setup.ts
const React = require('react');
if (!React.act) {
  React.act = (cb: () => void) => cb();
}
```

Works for simple synchronous rendering. May not cover async act().

### C. Exclude Test Files from tsconfig.app.json

```json
"exclude": ["src/**/*.test.ts", "src/**/*.test.tsx"]
```

Prevents TS errors from `ComponentType` callability issues in test files.
Vitest handles test compilation independently.

### D. vitest.config.ts for jsdom

```ts
import { defineConfig } from 'vitest/config';
export default defineConfig({
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}'],
    setupFiles: ['./vitest.setup.ts'],
  },
  resolve: {
    conditions: ['browser', 'import', 'module', 'default'],
  },
});
```

## Common jsdom Mocks

```ts
// matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false, media: query, onchange: null,
    addListener: () => {}, removeListener: () => {},
    addEventListener: () => {}, removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

globalThis.IS_REACT_ACT_ENVIRONMENT = true;
```

## Library Mock Patterns

```ts
// CodeMirror
vi.mock('@codemirror/view', () => ({ EditorView: vi.fn(), basicSetup: [] }));
vi.mock('@codemirror/lang-javascript', () => ({ javascript: () => [] }));

// TanStack Table
vi.mock('@tanstack/react-table', () => ({
  useReactTable: () => ({ getHeaderGroups: () => [], getRowModel: () => ({ rows: [] }) }),
  getCoreRowModel: () => ({}),
  flexRender: () => '',
  createColumnHelper: () => ({ accessor: (key, opts) => ({ id: key, header: opts.header ?? key, cell: () => '' }) }),
}));
```
