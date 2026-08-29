# `dsh plugin add` failures (CLI path, not the dshmarket UI path)

The `dsh plugin add <pkg>` command shells out to `pnpm` in the profile dir. It hits **three independent traps** that each look like the same "pnpm failed" exit. Verify which one you're in before fixing.

Quick triage:
```bash
cd ~/.dsh/profiles/web
pnpm --version                # 1: store mismatch if not v11.x
grep -B1 -A4 '^  dsh-pack-maker@' pnpm-lock.yaml   # 2: integrity in resolution? field?
grep -A2 "fetchTimeout\|RetryOperation" ~/.npm-global/lib/node_modules/pnpm/dist/pnpm.mjs | head -3   # 3: string-vs-number AbortSignal.timeout
```

## Trap 1 — pnpm store version mismatch (`ERR_PNPM_UNEXPECTED_STORE`)

`dshmarket` (and now the official profile bootstrap) install with **pnpm 11** and link into `~/.local/share/pnpm/store/v11`. If your PATH `pnpm` is an older v10 (`pnpm --version` prints `10.x`), every command aborts:
```
ERR_PNPM_UNEXPECTED_STORE  Unexpected store location
The dependencies at ".../node_modules" are currently linked from the store at ".../store/v11".
Pnpm now wants to use the store at ".../store/v10"...
```

**Fix:** `npm i -g pnpm@latest`. Confirm `pnpm --version` prints `11.x`. Do not touch the store dirs.

## Trap 2 — `pnpm-lock.yaml` integrity missing for GitHub-release tarballs

pnpm 11 enforces supply-chain verification (`ERR_PNPM_MISSING_TARBALL_INTEGRITY`) on every lockfile entry. `dshmarket` declares its companion package `dsh-pack-maker` as a GitHub release tarball in its default bundle list; older lockfiles built before this enforcement lack an `integrity:` line in the `resolution:` field:

```yaml
# BROKEN (lockfile predates pnpm 11 enforcement)
dsh-pack-maker@https://github.com/.../dsh-pack-maker-0.1.3.tgz:
    resolution: {tarball: https://github.com/.../dsh-pack-maker-0.1.3.tgz}
    version: 0.1.3

# FIXED — integrity inlined INSIDE resolution: {...}
dsh-pack-maker@https://github.com/.../dsh-pack-maker-0.1.3.tgz:
    resolution: {tarball: https://github.com/.../dsh-pack-maker-0.1.3.tgz, integrity: sha512-...}
    version: 0.1.3
```

`pnpm install --fix-lockfile` does NOT repair this. `pnpm add --no-frozen-lockfile` rewrites the lockfile but still writes integrity on its own line — pnpm expects it inlined in `resolution: {...}`.

**Fix:** compute sha512 of the tarball and inline it into the `resolution:` value.
```bash
URL='https://github.com/publieople/dsh-pack-maker/releases/latest/download/dsh-pack-maker-0.1.3.tgz'
curl -sSL -o /tmp/pkg.tgz "$URL"
INT=$(openssl dgst -sha512 -binary < /tmp/pkg.tgz | openssl base64 -A)
INT="sha512-$INT"
# Then edit pnpm-lock.yaml: change `resolution: {tarball: <URL>}` to
# `resolution: {tarball: <URL>, integrity: <INT>}`
```
Pattern, not exact text — apply per offending entry; check `grep 'resolution: {tarball:' pnpm-lock.yaml | grep -v integrity` to enumerate them.

After patching, `pnpm add <pkg>` returns `✓ Lockfile passes supply-chain policies`.

## Trap 3 — `dsh plugin` CLI does not forward `RELEASE_AGE_OVERRIDE` (the upstream gap)

`dshmarket`'s HTTP routes inject `--config.minimumReleaseAge=0` (`RELEASE_AGE_OVERRIDE` in `dshmarket/src/install.ts`) for every add/install/update. **The CLI path does not.** Look at `~/.npm-global/lib/node_modules/@deepseek-ai/dsh/lib/bin.js`:
```js
program.command("plugin")...argument("[args...]", "pnpm arguments, forwarded verbatim")...
    .action((args, options) => { resolved = { mode: "plugin", profile: options.profile, args }; });
```
No override injection. So `pnpm-workspace.yaml`'s `minimumReleaseAge: 1440` (1 day) blocks every freshly-published bundle the marketplace ships — `@anionex/*`, `@linxin666/*`, etc.

Symptom: `Lockfile contains entries that the active policies reject. ... MINIMUM_RELEASE_AGE_VIOLATION`.

**Fix:** patch `bin.js` to inject the override for `add | install | update | remove`. `remove` must be included — it re-verifies the entire lockfile and trips the same cutoff.
```js
const sub = args[0];
const overrideFlags = ["--config.minimumReleaseAge=0"];
const patchedArgs = (sub === "add" || sub === "install" || sub === "update" || sub === "remove")
    ? [sub, ...overrideFlags, ...args.slice(1)]
    : args;
resolved = { mode: "plugin", profile: options.profile, args: patchedArgs };
```
Mark with a `ponytail:` comment naming the ceiling ("Remove when dsh upstream forwards RELEASE_AGE_OVERRIDE itself") so the patch intent is recoverable.

**Caveat with `--config.fetchTimeout=…`:** pnpm 11 reads `--config.fetchTimeout=<value>` as a string and pipes it to `AbortSignal.timeout(...)`, which demands `number`. Result: `TypeError [ERR_INVALID_ARG_TYPE]: The "delay" argument must be of type number. Received type string ('600000')` looping forever inside retry. Do NOT add this flag. pnpm's default 60s fetchTimeout is enough for normal `add` (single new dep, ~5s total).

**Caveat with `--config.X` placement:** Commander treats `--config.X` as an unknown option but `--profile <name>` is `requiredOption`. `--profile` MUST come before any forward-through args, otherwise commander treats `--config.X` as the profile name and initializes a profile dir at `~/.dsh/profiles/--config.X/`. Inside the patched bin.js (where commander has already parsed), appending the flag after `sub` is safe.

**Caveat: `npm i -g @deepseek-ai/dsh@latest` will overwrite the bin.js patch.** Either:
- Repeat the patch after every dsh upgrade
- Submit the fix upstream (`dshmarket/src/install.ts` already has the pattern; `bin.js` just needs to forward it)
- Wrap with a shell alias that injects `--config.minimumReleaseAge=0` yourself

## Diagnostic order for `dsh plugin add` failures

1. `pnpm --version` — must be 11.x; `npm i -g pnpm@latest` if not.
2. `grep '^    resolution:' ~/.dsh/profiles/web/pnpm-lock.yaml | grep -v integrity` — every GitHub-tarball entry with no inlined integrity is a Trap 2 case.
3. Repeat the exact command with `pnpm` directly (bypassing `dsh plugin`) and the override flags to confirm:
   ```bash
   cd ~/.dsh/profiles/web && pnpm --config.minimumReleaseAge=0 add <pkg>
   ```
   - Still fails with `MINIMUM_RELEASE_AGE_VIOLATION` → CLI flag not reaching pnpm (Trap 3 not patched, or `--profile` arg ordering).
   - Fails with `MISSING_TARBALL_INTEGRITY` → Trap 2.
   - Succeeds → `dsh plugin` was the wrapper problem (Trap 3).