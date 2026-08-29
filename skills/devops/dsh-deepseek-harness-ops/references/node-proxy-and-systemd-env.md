# Node global `fetch` ignores HTTP_PROXY — and systemd env inheritance

Generalized lesson from the dsh plugin-market timeouts. Applies to ANY Node service
run under systemd whose child depends on `HTTP_PROXY`/`HTTPS_PROXY`.

## The two independent traps

1. **Node's global `fetch` does NOT honor `HTTP_PROXY`/`HTTPS_PROXY`.** Those env vars
   are read by `undici`'s `EnvHttpProxyAgent` (and by fetch libraries that opt into it),
   not by the built-in `globalThis.fetch`. The built-in fetch always connects direct.
   A library can add proxy support by importing undici explicitly and setting a
   dispatcher:
   ```js
   import { EnvHttpProxyAgent, fetch as undiciFetch } from 'undici';
   envProxyAgent ??= new EnvHttpProxyAgent();
   return undiciFetch(url, { ...init, dispatcher: envProxyAgent });
   ```
   `setGlobalDispatcher` from the undici PACKAGE does NOT affect `globalThis.fetch` —
   that runs on Node's INTERNAL copy of undici, a separate instance. Must call undici's
   own `fetch` with an explicit dispatcher.

2. **systemd user/system services inherit NO proxy env from your shell.** `export
   HTTP_PROXY=...` in login/bashrc only reaches processes you spawn from that shell.
   systemd spawns units with exactly the env you declare via `Environment=`,
   `EnvironmentFile=`, or the manager's `DefaultEnvironment`. A unit that needs the
   proxy must declare it literally:
   ```
   Environment=HTTP_PROXY=http://127.0.0.1:7890
   Environment=HTTPS_PROXY=http://127.0.0.1:7890
   ```

## Failure signature
- Works when you run the binary by hand in a shell that has proxy exported.
- Times out (often ~30s, sometimes with "N attempts") when the same binary runs under
  systemd.
- `curl` behaves differently from the app: curl reads proxy env / `-x`, so curl may
  succeed direct or via proxy while the Node app (built-in fetch, no dispatcher) hangs.

## Confirmation
Check the running process's actual environment:
```bash
cat /proc/<pid>/environ | tr '\0' '\n' | grep -i proxy
```
Empty → unit lacks the proxy env; add `Environment=` lines, `daemon-reload`, restart,
re-check. Proxy env is read at process startup, so restarting is mandatory.

## When proxy env IS set but you still want direct (or per-host bypass)
`no_proxy`/`NO_PROXY` is honored by EnvHttpProxyAgent. Add e.g.
`Environment=NO_PROXY=127.0.0.1,localhost` to keep loopback calls off the proxy.

## Verify without a browser
For an HTTP-serving Node app, curl the app's own health/market endpoint and confirm a
fast 200 rather than a timeout. That proves the app process can reach what it needs,
independent of the UI.