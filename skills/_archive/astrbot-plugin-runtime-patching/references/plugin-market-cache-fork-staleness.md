# AstrBot plugin market cache fork-staleness

## Symptom

AstrBot WebUI → 插件市场 shows plugin X at version v1.0.3. The plugin's
GitHub repo (`master` branch `metadata.yaml`) is at v1.1.1. Restarting
AstrBot (`sudo systemctl restart astrbot`) does **not** refresh the
displayed version. The plugin keeps reporting "old version" in market.

## Why it happens

AstrBot's plugin market has three pieces:

1. **MD5 endpoint** — `https://api.soulter.top/astrbot/plugins-md5`
2. **Index endpoint** — `https://api.soulter.top/astrbot/plugins`
   (primary) plus GitHub fallback
   `https://github.com/AstrBotDevs/AstrBot_Plugins_Collection/raw/refs/heads/main/plugin_cache_original.json`
3. **Local cache** — `{data_dir}/plugins.json` (and
   `{data_dir}/plugins_custom_<md5-prefix>.json` for user-added registries)

On every market fetch, AstrBot compares the MD5 it gets from (1) against
the MD5 stored inside the local cache file. Only on mismatch does it pull
the fresh index from (2). If MD5 matches, the cached version is used
verbatim.

The index tracks plugins by their **original author**. When a plugin's
repo is forked (e.g. `FlanChanXwO` → `iona-s`) and the new maintainer
doesn't push a PR to
[`AstrBotDevs/AstrBot_Plugins_Collection`](https://github.com/AstrBotDevs/AstrBot_Plugins_Collection),
the index never learns about the new repo. The market permanently shows
the original repo's last published version (here v1.0.3) regardless of
how many new versions the fork has.

This is independent of:
- AstrBot core version (upgrading AstrBot does not refresh market data)
- Local plugin install state (uninstalling/reinstalling the plugin does
  not refresh market data)
- Bot restart (no MD5 change → cache used)

## How to confirm it's the cache and not a real old version

```bash
# Local install version
cat /home/po/astrbot/data/plugins/<name>/metadata.yaml | grep version

# Cached market version
grep -A 6 "<original_author>/<name>" /home/po/astrbot/data/plugins.json
# look at the "version" key inside the entry

# Upstream actual version (replace <author>/<repo>)
curl -fsSL https://raw.githubusercontent.com/<author>/<repo>/master/metadata.yaml | grep version
```

If `data/plugins.json` shows v1.0.3 and upstream shows v1.1.1, the cache
is stale.

## Fixes (in order of laziness)

### 1. Manual clone (skip the market, install from the new repo)

```bash
cd /home/po/astrbot/data/plugins
rm -rf <name>
git clone https://github.com/<new_author>/<repo>.git
```

Then reload in WebUI 插件页 or `sudo systemctl restart astrbot`. The
local install is now v1.1.1. **Market display stays at v1.0.3** — that's
fine, the cache is harmless once the actual plugin code is correct.

### 2. Add a custom registry source

WebUI → 插件市场 → 设置 → 插件安装源 → add a new source pointing at a
JSON index that lists the new fork. AstrBot stores its cache for this
custom source under
`{data_dir}/plugins_custom_<md5(url)[:8]>.json`. Then WebUI can install
from the fork via the market UI. This is the right approach if the user
adds new plugins from this fork often.

### 3. Upstream fix (slowest, cleanest)

PR
[`AstrBotDevs/AstrBot_Plugins_Collection`](https://github.com/AstrBotDevs/AstrBot_Plugins_Collection)
to update the entry's `repo` field to the new fork's URL. Once merged,
the next MD5 mismatch refresh will pull the new index. Until then,
every AstrBot installation on Earth will show v1.0.3 in market.

## Don't do this

- **Don't `rm /home/po/astrbot/data/plugins.json`** hoping the next
  fetch will rebuild it from upstream. The fetch IS based on MD5
  comparison, not on cache absence — empty cache + stale MD5 endpoint
  just means "use empty cache". Worse, you also wipe the cache of every
  other plugin you have installed via the market.
- **Don't patch `data/plugins.json` to bump the version manually**.
  It's a JSON manifest used by the WebUI; tampering with it desyncs
  display state from install state and breaks "更新" button logic.