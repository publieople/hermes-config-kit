---
name: minecraft-modpack-startup-hang
description: Diagnose Forge 1.18-1.20 modpack clients (PCL2/HMCL/MultiMC) that hang at startup — no crash, no main menu, splash freezes. Trigger on "卡住", "hang", "stuck loading", "won't enter main menu", "启动卡死", "整合包启动不动".
---

# Minecraft Modpack Startup Hang Diagnosis

When a Forge modpack client hangs during startup without crashing, the cause is almost always at a specific phase. This skill covers triage and binary-search diagnosis using PCL2 logs.

## When to use

- User reports: "卡住 / hang / stuck at loading / 不进主菜单 / 启动卡死"
- Splash screen sits forever, no crash dialog, no error
- User has already tried disabling the most recently added mods (strong signal their correlation is wrong)

## First pass — extract evidence before hypothesizing

### Locate logs

PCL2 (most common on Chinese desktops) writes to the version directory:

```
E:\.minecraft\versions\<versionName>\logs\
  debug.log           # full binary-ish, use `strings`
  latest.log          # human-readable tail
  debug-1.log.gz ... debug-5.log.gz  # rotated boots
```

HMCL / MultiMC use similar structures under their own roots.

### Three facts in order

**1. Actual Java version used** — not the launcher's preference:

```bash
strings "<gameDir>/logs/debug.log" | head -3 | grep "java version"
```

Then cross-check with `%AppData%\PCL\config.json` → `JavaList[]`. PCL2 default-uses `java-runtime-delta` (Java 21) even when the version JSON declares `java-runtime-gamma` (Java 17). The user setting may not match the running version.

**2. Hang phase** — `tail -c 5000` of debug.log:

```bash
tail -c 5000 "<gameDir>/logs/debug.log"
```

Look for the **ModernFix 60s worker shutdown signature** — if you see `Worker-ResourceReload-N shutdown` lines at **exactly 60s intervals** with no `[Worker-Main/INFO] Setting up` or `Loaded X mods` between them, the hang is in the **resource reload listener completion phase**. This is the most common Forge 1.19.2 hang location.

**3. Verify user-claimed mods are actually loaded this boot:**

```bash
strings "<gameDir>/logs/debug.log" | grep -ciE 'modname1|modname2|modname3'
```

If 0 hits, the mods were never loaded. PCL2 / CurseForge convention: `.jar.disabled` = skipped, zero log noise. The user's "I disabled them and it still hangs" is actually **"they were already not loaded"**, which means the hang is somewhere else — almost certainly in pack-bundled mods the user never touched.

## Hang signature → likely suspects

If silence starts after `Reloading ResourceManager:` and 60s ModernFix shutdowns follow, the culprit is one of these reload listeners:

| Phase | Suspect | Verify |
|---|---|---|
| Late ModelBakery / TextureAtlas | corrupt PNG inside a mod jar | grep `Could not load image: Corrupt PNG` near the silence |
| KubeJS asset regeneration | `ponderjs-*.jar` (Create ponder scene generator) synchronously re-emits JSON during reload | `ls kubejs/assets/ponderjs_generated/` (if present, suspect); grep `[KubeJS/]: Found plugin source ponderjs` in log |
| Shader pack init | `oculus-*.jar` + `embeddium-*.jar` combination (known: Asek3/Oculus #691) | both jars present + shaderpack selected |
| ModernFix cache wait | `modernfix-forge-*.jar` with `mixin.perf.dynamic_resources=true` | grep `modernfix-mixins.properties` for that key (default false) |
| Resource reload deadlock | `Create` + huge config; `farmersdelight` + `create_central_kitchen` mixin targets not satisfied | grep `Mixin target ... was not found` for missing classes |

## Binary search via `.disabled`

PCL2 / CurseForge convention: rename `mods/<mod>.jar` → `mods/<mod>.jar.disabled` to skip it.

1. **Start with the suspect the evidence table points to, NOT the user's mods** — those were already tried.
2. Disable one → restart → observe:
   - Hang time shortens or game enters main menu → that mod contributed, narrow in
   - Hang signature identical → wrong mod, re-enable, try next
3. For PonderJS specifically: `mods/ponderjs-1.19.2-*.jar` → `.disabled`. If game enters main menu, that's the hang.
4. For embeddium+oculus: disable `oculus-*.jar` first (o is the higher-risk side); if still hangs, disable `embeddium-*.jar`.

## Anti-patterns

- **Don't trust Java version blame without verifying** the actual launched Java. Java 21 → 17 switch only helps if the pack needs Java 17 module exports. For resource reload hangs, Java version rarely matters — verify with the `strings | grep` above before recommending the swap.
- **Don't recommend disabling the user's mods first.** They were already tried. The hang is likely in pack-bundled mods.
- **Don't suggest multiple changes at once.** Each test's diagnostic value vanishes if 3 things changed.
- **Don't ask for a thread dump.** This is a Windows client, no easy jstack path from WSL, and the 60s ModernFix signature already localizes the phase.
- **Don't recommend RAM increases** for this signature. The hang is not GC pressure, it's a listener never returning.

## Verification of fix

After removing the culprit, the boot should show:
- `[Render thread/INFO] ... Reloading complete` or `[main] Setting up ... MainMenuScreen`
- `[main/INFO] ... Loaded X mods`

If the user reports "still hangs after disabling X", binary search continues. The signature (60s cadence) stays the same only if the wrong mod was disabled.

## Reference

See `references/forge-1192-hang-signatures.md` for exact log strings to grep for and a worked example.