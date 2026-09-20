# Forge 1.19.2 Resource Reload Hang — Signatures & Worked Example

## ModernFix 60s worker-shutdown signature (diagnostic gold)

When Forge's `ReloadableResourceManager.reload()` is waiting on a reload
listener that never returns, **ModernFix logs every worker's shutdown at
exactly 60s intervals**. The pattern:

```
01:25:52.xxx  [Worker-ResourceReload-N] ... (lots of ModelBakery work)
01:26:52.xxx  [Worker-ResourceReload-4/DEBUG] [ModernFix/]: Worker-ResourceReload-4 shutdown
01:27:52.xxx  [Worker-ResourceReload-8/DEBUG] [ModernFix/]: Worker-ResourceReload-8 shutdown
01:28:52.xxx  [Worker-ResourceReload-0/DEBUG] [ModernFix/]: Worker-ResourceReload-0 shutdown
```

- 60s cadence = `awaitQuiescence` on the reload instance, then per-worker timeout close.
- If this is the **last thing in the log** and never followed by `[main] Setting up ... MainMenuScreen` or `Loaded X mods`, the hang is in reload.
- If you see this signature across multiple boots with identical timestamps, the same listener is wedged every time.

## "User disabled the suspicious mod" trap

User reports: "I disabled mods X, Y, Z and it still hangs."

PCL2 / CurseForge convention: `*.jar.disabled` = skipped entirely, **zero log output for that mod**. Verify:

```bash
strings "<gameDir>/logs/debug.log" | grep -ciE 'modname1|modname2|modname3'
```

If 0: those mods never loaded → user's correlation was wrong → look at pack-bundled mods instead.

Concrete example: `ultimine` / `mousetweak` / `customskin` 0 hits in a 2.5MB debug.log meant the user spent time disabling the wrong mods.

## Java version actually used vs launcher preference

PCL2 (`%AppData%\PCL\config.json` → `JavaList[]`) often defaults to **Java 21 (delta runtime)** even when the version JSON declares `java-runtime-gamma` (Java 17). The first boot may use Java 21; switching to Java 17 doesn't necessarily change anything if the hang is in reload listeners (Java 21 module exports only matter for `jdk.internal.misc.Unsafe` access during early netty init, which ModernFix falls back from).

Verify with:

```bash
strings "<gameDir>/logs/debug.log" | head -3 | grep "java version"
```

## Phase-by-phase log anchors (in order)

1. **ModLauncher start** — `ModLauncher 10.0.8 starting: java version`
2. **Transform services** — `Found transformer services : [mixin,fml,hotai,I18nUpdateMod]`
3. **Mod loading** — `Creating FMLModContainer instance for ...`
4. **Forge init** — `MinecraftForge v<ver> Initialized`
5. **Client setup** — `[FANCYMENU] Registering resource reload listener..` (if FancyMenu present)
6. **Resource reload START** — `Reloading ResourceManager: Default, Mod Resources, ...`
7. **Reload workers** — many `[Worker-ResourceReload-N] ...` entries
8. **Reload END** — should appear as `[Render thread/INFO] ... Reloading ResourceManager complete` (or similar). **If absent, hang is here.**
9. **Main menu** — `[main/INFO] ... Setting up ... MainMenuScreen`
10. **Mods loaded** — `Loaded <N> mods`

Stop counting at step 8 if step 9 never appears.

## Specific reload-listeners known to hang on 1.19.2 packs

| Mod | Why it hangs | File to disable |
|---|---|---|
| `ponderjs-1.19.2-*.jar` | Synchronously regenerates `kubejs/assets/ponderjs_generated/` during reload | `mods/ponderjs-1.19.2-1.2.0.jar` |
| `oculus-*.jar` + `embeddium-*.jar` | Resource finalize deadlock (Asek3/Oculus issue #691) | disable oculus first |
| `ModernFix` `mixin.perf.dynamic_resources=true` | Async cache wait never completes | revert to false |

## Worked example (real session)

User: "I added 3 helper mods and the game hangs. I disabled them and it still hangs."

1. `ls mods/` — found `[连锁破坏] ftb-ultimine-forge-...jar.disabled` ×3 (renamed by user).
2. `strings debug.log | grep -ciE 'ultimine|mousetweak|customskin'` → **0** (proof: mods never loaded this boot).
3. `head -3 debug.log | grep "java version"` → `java version 21.0.3 by Microsoft` (PCL2 default).
4. Switched user to Java 17 — **still hangs**, identical signature.
5. `tail -c 5000 debug.log` → `01:28:52 Worker-ResourceReload-0 shutdown`, no main menu log.
6. Suspicion narrowed to KubeJS `ponderjs_generated` (Create ponder scene generator) — PonderJS registered as a reload listener that synchronously re-emits JSON for every scene.

Fix: `mods/ponderjs-1.19.2-1.2.0.jar` → `.disabled`, restart.

## Anti-patterns in this debug session

- Hypothesized "Java 21 + Forge 1.19.2 module exports" before verifying the log actually showed the hang signature. Java version mattered less than thought; switching wasted a boot.
- Let the user's "I disabled mods X" framing bias suspect list away from the pack's own mods. The framing was wrong (mods were already disabled), so the suspect list was wrong.
- Should have grepped for the disabled mods first, before recommending Java changes.