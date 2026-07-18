# SPC 8.x + Modrinth modpacks — known gap

Captured from `Chapter of Yuusha 3` (MC 1.20.1 + Forge 47.4.13) deployment, 2026-07-13.

## Symptom

SPC 8.x reports success (`Successfully generated Server Pack: ...`) but the resulting `mods/` folder is mostly empty compared to the source modpack.

## Cause

SPC 8.x's clientside-only fallback list (built-in, hardcoded in `de.griefed.serverpackcreator.api.utilities.common`) is aggressive — it treats most content mods (Aether, Apotheosis, Aquaculture, Twilight Forest, etc.) as "client-only" and strips them from the server pack output.

Crucially, SPC 8.x downloads mods **only from the modpack manifest** (modrinth.index.json or manifest.json), not from the local modpack source directory's `overrides/` or `mods/` folders. So even if the user has the jars locally, SPC will not include them in the server pack.

## Numbers (the Chapter of Yuusha 3 case)

| Bucket | Count |
|---|---|
| Client mods/ (full set, what the player runs) | 316 |
| modrinth.index.json files[] (declared mods) | 281 |
| SPC output mods/ (after -cgen + -config + run) | **38** |
| Mods missing from server pack | 278 |
| Of the 38, missing transitive deps | 8 (farmersdelight, curios, enigmaticlegacy, octolib, architectury, celestial_core, configapi, distant_worlds) |
| Of those 8, missing second-order deps | 3 (geckolib, patchouli, caelus) |
| Server mods/ after manual scp of 11 jars | 49 |
| **Server still short** | **232** |

## Reproduction recipe

1. `unzip -p modpack.zip modrinth.index.json | python3 -c "import json,sys; j=json.load(sys.stdin); print(len(j.get('files',[])))"` → gives manifest count
2. Run SPC end-to-end as documented in SKILL.md
3. `ls -1 output/mods/ | wc -l` → likely much less than manifest count

## Working fix: scp from client mods/

```bash
SRC="/mnt/e/.minecraft/versions/<modpack name>/mods"
DST="user@server:~/.../server/mods"
for f in "<mod1>.jar" "<mod2>.jar" ...; do
  scp -P <port> "$SRC/$f" "$DST/"
done
```

Match the mod name in the server boot log "Missing or unsupported mod: '<name>'" to the client jar (case-insensitive, fuzzy on version).

### Matching notes (Chapter of Yuusha 3 specific)

- `farmersdelight` ← client has `FarmersDelight-1.20.1-1.2.8.jar` (NOT `farmersrespite`)
- `curios` ← `curios-forge-5.14.1+1.20.1.jar`
- `enigmaticlegacy` ← `EnigmaticLegacy-2.30.1.jar` (the original, NOT the `-Modification` fork)
- `architectury` ← `architectury-9.2.14-forge.jar`
- `distant_worlds` ← `DistantWorlds-Reborn-1.20.1-v1.1.0-Beta.jar`

Version check (from server log version constraint):
- patchouli: need 1.19.2-77+, client has 1.20.1-84 → OK
- caelus: need 1.19.2-3.0.0.6+, client has 3.2.0+1.20.1 → OK
- octolib: any version, client has 0.5.0.1 → OK

## When to fall back to scp vs. re-run SPC

- New server pack from a fresh client install → use SPC (it's the "official" path)
- Existing deployed server missing mods after a client update → use scp
- First-time setup with a heavily modded modpack → expect scp as a second step; don't trust SPC's "Done!" message as completion
