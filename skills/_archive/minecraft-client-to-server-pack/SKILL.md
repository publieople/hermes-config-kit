---
name: minecraft-client-to-server-pack
description: Use ServerPackCreator (Griefed) CLI to convert a Minecraft client modpack (CurseForge .zip or Modrinth .mrpack) into a runnable server pack. Java 21, Arch/WSL friendly. Outputs zip + flat directory with start.sh/.bat/.ps1 + server.properties. Use when user has a client modpack and needs a server-side jar/scripts.
---

# Minecraft client modpack → server pack

Convert a **client modpack** (the one a player launches) into a **server pack** (the one a server runs) using Griefed's ServerPackCreator (SPC).

## When to use

- User says "把这个整合包做成服务端" / "generate server pack from this modpack" / "client 转 server"
- Has a modpack zip / extracted dir; wants a deployable server pack

## When NOT to use

- User has a **server pack** already (zip with `start.sh`, `mods/`, `server.properties`) → use official `gaming/minecraft-modpack-server` skill instead
- User wants to host on a public server with port-forwarding → official skill covers deployment

## Prerequisites

| Item | Notes |
|---|---|
| Java 21 (JDK) | `sudo pacman -S jdk21-openjdk` (Arch) / `apt install openjdk-21-jdk` (Debian) |
| SPC jar | Download from https://github.com/Griefed/ServerPackCreator/releases (latest, e.g. `ServerPackCreator-8.1.2.jar`) — GUI download is more reliable than WSL curl/gh release (gh release asset URL has JWT expiry that breaks wget resume) |
| Modpack | CurseForge zip OR Modrinth .mrpack OR extracted dir |

## Workflow (3 commands)

### 1. Unpack if needed

```bash
# Point modpackDir at the LAUNCHER INSTANCE (PCL/MultiMC/Prism/CurseForge App),
# NOT a zip-extracted directory. PCL instance:
#   E:\.minecraft\versions\Chapter of Yuusha 3\
#   ├─ mods/            ← server needs this
#   ├─ config/          ← server needs this
#   ├─ modrinth.index.json   (or manifest.json for CurseForge)
#   └─ ...
#
# If you extract the zip instead, you get a layout like:
#   modrinth.index.json
#   overrides/  (Modrinth) or mods/ + config/ (CurseForge)
# ...and SPC will treat it as a DIFFERENT code path.
```

### 2. Generate config (interactive, but only on first run)

```bash
java -jar ~/spc/spc.jar -cgen ~/spc/work/modpack_src -config ~/ServerPackCreator/configs/<name>.conf
```

`-cgen` writes the conf but does NOT fill `minecraftVersion` / `modLoader` / `modLoaderVersion` from the modpack manifest — fill these manually:

- For **Modrinth** modpacks: read `modpack_src/modrinth.index.json` → `dependencies.minecraft`, `dependencies.forge`/`fabric`/`quilt`
- For **CurseForge** modpacks: read `modpack_src/manifest.json` → `minecraft.modLoaders[].id`, `minecraft.version`

Edit `~/ServerPackCreator/configs/<name>.conf` → set the 3 fields.

### 3. ⚠️ The TWO traps: `inclusions` field AND `modpackDir` choice

**Trap 1 — `modpackDir` wrong → wrong code path:**

| `modpackDir` points to | SPC sees | Result |
|---|---|---|
| **PCL instance dir** (`.../versions/<name>/`) | `mods/` + `config/` + manifest at top | Treats as installed modpack → all jars, full ~315 mod server pack |
| **Zip-extracted dir** (`.../work/modpack_src/`) | `overrides/` + manifest at top | Treats as modrinth staging → only downloads modrinth manifest mods → ~38 mod server pack (broken) |

**Use the launcher instance dir, not the zip-extracted dir.** On WSL: `modpackDir = "/mnt/e/.minecraft/versions/Chapter of Yuusha 3"`. On Windows GUI: `modpackDir = "E:\.minecraft\versions\Chapter of Yuusha 3"`.

**Trap 2 — `inclusions` empty → empty server pack:**

`-cgen` produces `inclusions = []`. Without filling this, SPC exits with:

```
ERROR: No directories or files specified for copying. This would result in an empty serverpack.
```

Format (InclusionSpecification: source/destination, no filters needed). **Source path differs by which dir you pointed at:**

```ini
# For PCL instance dir (modpackDir = .../versions/<name>/):
inclusions = [
  {source="config",         destination="config"},
  {source="defaultconfigs", destination="defaultconfigs"},
  {source="modernfix",      destination="modernfix"},
  {source="mods",           destination="mods"},
  {source="scripts",        destination="scripts"}
]

# For zip-extracted Modrinth dir (modpackDir = .../work/modpack_src/):
inclusions = [
  {source="overrides/config",         destination="config"},
  {source="overrides/defaultconfigs", destination="defaultconfigs"},
  {source="overrides/mods",           destination="mods"},
  {source="overrides/scripts",        destination="scripts"},
  {source="overrides/options.txt",    destination="options.txt"}
]
```

**Add every directory the modpack wants to carry to the server.** Inspect the directory you pointed at to find what to include (`ls` on it).

### 4. Generate server pack

```bash
java -jar ~/spc/spc.jar -config ~/ServerPackCreator/configs/<name>.conf \
  --destination ~/spc/output
```

Output:
- `~/spc/output/` — flat server dir
- `~/spc/output_server_pack.zip` — ready-to-upload zip

## Verifying it worked

```bash
ls ~/spc/output/  # MUST contain: start.sh, start.bat, start.ps1, mods/, config/, server.properties, install_java.sh
unzip -l ~/spc/output_server_pack.zip  # sanity check: 10k+ entries, ~200-300MB
```

Log lines to look for (success):
```
ConfigurationHandler.kt: Config check successful. No errors encountered.
ServerPackHandler.kt: Copying files to the server pack...
ServerPackHandler.kt: Creating zip archive of serverpack...
ServerPackHandler.kt: Finished creation of zip archive.
Successfully generated Server Pack: ...
```

## Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `SPC headless tty ioctl` error in background log | Hermes sandbox kills the process | Run `java -jar ... < /dev/null > log 2>&1` **foreground** with `timeout 600`; 5–10 min runtime is normal |
| `curl/gh release` downloads truncated to ~33MB of 78MB | gh release asset URL has JWT expiry; WSL proxy is slow | Download via Windows browser to `C:\Users\po\Downloads\`, then `cp` to WSL |
| `No directories or files specified` | `inclusions = []` from `-cgen` | See Step 3 above |
| `Can not connect to maven.legacyfabric.net` warnings | LegacyFabric maven is slow/unreliable from CN | Warnings only — ignore if `forge-manifest.json`/`fabric-manifest.xml` say "does not need to be refreshed" |
| Output server pack has no `minecraft_server.jar` / `forge-*-installer.jar` | SPC 8.x does NOT auto-install server jar; it only packages mods/config/scripts | First server boot (`./start.sh`) downloads them; needs internet. For offline: pre-download to `output/` manually |
| WSL cp 240MB+ zip to `/mnt/e/` stalls | NTFS mount is slow/unstable for big single files | Use PowerShell: `Copy-Item '\\wsl$\<distro>\home\po\spc\output_server_pack.zip' C:\Users\po\Downloads\`

## Notes for re-runs

- Home dir `~/ServerPackCreator/` is created on first run; reused after
- Manifests cached in `~/ServerPackCreator/manifests/`; refresh ~daily
- Re-running with same conf is safe (default `cleanupOfAlreadyExistingServerPacks=true`)
- For CurForge modpacks the source dir is the modpack root, not `overrides/` — adjust inclusions accordingly

## ⚠️ Real-world behavior gap (SPC 8.x with Modrinth modpacks)

Tested against `Chapter of Yuusha 3` (1.20.1 + Forge 47.4.13, Modrinth, 316 client mods):

- modrinth manifest listed **281** mods; SPC output had only **38 mods**
- The other 278 were stripped (SPC 8.x's clientside-only fallback list is aggressive — it classifies most content mods as client-only)
- Of the 38, 8 were missing transitive deps; 3 more missing second-order deps (geckolib / patchouli / caelus)
- **Net: server still 232 mods short of a complete server pack**

**Don't trust SPC output as complete for Modrinth modpacks.** SPC 8.x was redesigned to only download mods listed in the modpack manifest from the upstream registry — it does NOT include extras from the local `overrides/` mods folder even if the user has them. The workflow above is the **packaging mechanics**; this section is the **operational reality**.

## When SPC output is incomplete — manual scp fallback

The **client install** (the one the player launches) always has the full mod set. When the server is missing mods, fix by copying from client to server, not by re-running SPC.

1. SSH into the server, read the boot log, find the "Missing or unsupported mod" line
2. Match the mod name to a jar in the **client** mods/ directory
3. `scp` it to the server's `mods/`
4. Restart; repeat for the next missing mod

This is faster than re-running SPC for a deployed server. Use SPC for the **initial** server pack; use scp for **patching**.

Nuclear option when many mods are missing: `scp client/mods/*.jar server:/.../mods/`. Server will load client-only mods (JEI, OptiFine, Iris) as server-side no-ops or warnings, but the world will boot.

See `references/spc-8x-modrinth-gap.md` for the full Chapter of Yuusha 3 transcript (mod counts, dep chains, exact scp command).
