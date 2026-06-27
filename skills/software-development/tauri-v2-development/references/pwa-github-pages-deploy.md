# GitHub Pages PWA Deployment for Tauri Projects

Use this when deploying a Tauri project's PWA companion to GitHub Pages at a subpath.

## GitHub Actions Workflow

```yaml
# .github/workflows/deploy-pwa.yml
name: Deploy PWA to GitHub Pages

on:
  push:
    branches: [master]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}

    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v3
        with:
          version: 11
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm build
      - uses: actions/configure-pages@v4
      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist
      - id: deployment
        uses: actions/deploy-pages@v4
```

## Enable GitHub Pages

```bash
# Enable Pages with workflow-based deployment
gh api repos/:owner/:repo/pages -X POST -F "build_type=workflow"

# Check deployment status
gh run list --repo :owner/:repo --limit 3
```

## Vite Config for Subpath

```js
export default defineConfig({
  base: '/repo-name/',  // MUST match repo name for GH Pages subpath
  // ...
});
```

## Key Points

- `pnpm/action-setup@v3` must run before `setup-node`
- `cache: pnpm` on `setup-node` for dependency caching
- `concurrency: pages` prevents multiple simultaneous deploys
- `--frozen-lockfile` ensures CI uses exact dependency versions
- Custom domains (e.g., `for-people.cn/MDClipView/`) work automatically when configured at account level
