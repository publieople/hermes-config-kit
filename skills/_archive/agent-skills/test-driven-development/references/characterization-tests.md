# Characterization Tests: Adding Tests to Existing Code

## When to Use

The code already exists, works, and has ZERO tests. You're retrofitting a safety net — not doing greenfield TDD.

This is the most common real-world scenario for AI agents: user says "add tests to this project."

## How It Differs from Greenfield TDD

| Aspect | Greenfield TDD | Characterization Tests |
|--------|---------------|----------------------|
| Code exists? | No | Yes, and it presumably works |
| RED phase | Test fails because code is missing | Test fails because your assumption was wrong OR code has a bug |
| What to trust | The test (code doesn't exist yet) | The code (it's been running) |
| Failure response | Write code to pass | **First suspect the test is wrong**, then the code |
| Goal | Drive design | Establish safety net for refactoring |

## The Characterization Test Cycle

```
1. READ the source code thoroughly
2. WRITE a test asserting current behavior
3. RUN the test
   ├── PASSES → ✅ You correctly captured behavior
   └── FAILS → ⚠️ INVESTIGATE:
       ├── Test assumption wrong? → FIX THE TEST (most common)
       └── Actual bug found? → DOCUMENT, then fix with Prove-It pattern
4. REPEAT until all critical paths covered
```

## Critical Rule: Trust the Code First

When a characterization test fails, the DEFAULT hypothesis is "my test is wrong," not "the code is buggy."

**Example from open-any session:**

```typescript
// WRONG test assumption: 3-byte buffer of [0x00, 0x00, 0x00] is "too short for signature"
// → expected 'text', got 'hex'
// The code was RIGHT: 3 null bytes triggers null-byte binary detection
// FIX: use [0x41, 0x41, 0x41] (ASCII 'A') — short AND not binary
```

Only change the code if you can PROVE it's a bug with a standalone reproduction.

## What to Test First (Priority Order)

1. **Pure functions** — no side effects, deterministic, fastest to test
   - Format detection (extension maps, MIME maps, magic bytes)
   - Data transforms, validators, parsers

2. **State machines / classes with clear API** — register, resolve, clear
   - HandlerRegistry, caches, session managers

3. **Store actions** — zustand/redux actions with predictable state transitions
   - openFile, closeFile, updateBuffer

4. **Integration / async flows** — only after pure logic is covered

Save React components, DOM-dependent code, and E2E flows for later phases.

## Test File Placement

Colocate tests next to source:

```
src/utils/formatDetect.ts
src/utils/formatDetect.test.ts    ← alongside source
src/registry/registry.ts
src/registry/registry.test.ts     ← alongside source
```

This makes it obvious which files have coverage and which don't.

## Framework Selection

For Vite projects: use **vitest** (zero-config, same transform pipeline).

```bash
npm install -D vitest
```

Add to package.json:
```json
"scripts": {
  "test": "vitest run",
  "test:watch": "vitest"
}
```

## Test Naming Convention

DAMP (Descriptive And Meaningful Phrases) — each test reads like a specification:

```typescript
// ✅ Good: describes behavior, self-contained
it('detects PNG by magic bytes 89 50 4E 47', () => { ... })
it('returns hex when buffer contains more than 2 null bytes', () => { ... })
it('prioritizes extension over MIME', () => { ... })

// ❌ Bad: vague, requires reading the body
it('works with PNG', () => { ... })
it('handles binary', () => { ... })
it('test priority', () => { ... })
```

## Coverage Targets

For initial characterization:
- **Every extension/MIME/signature** in a static map → one test per entry (use `it.each` for bulk)
- **Every branch** in if/else logic → explicit test
- **Every state transition** in stores → explicit test
- **Edge cases**: empty input, null/undefined, max values, case sensitivity

Don't aim for 100% line coverage. Aim for **100% behavior coverage** — every observable behavior has a test.
