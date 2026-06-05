# Greenfield Multi-Skill Build Pipeline

实战证明有效的全套技能管线，用于从零搭建一个完整的 Next.js + shadcn + magicui 站点并部署上线。

## 管线总览

```
ui-ux-pro-max ──→ create-next-app ──→ shadcn init ──→ delegate_task ──→ build ──→ github deploy
  设计系统          项目脚手架           组件安装        并行写组件          验证      仓库+Pages
```

## 逐阶段详解

### Phase 0: 设计系统（必做）

在任何代码编写之前，先用 `ui-ux-pro-max` 生成完整设计系统：

```bash
cd ~/.hermes/skills/openclaw-imports/ui-ux-pro-max-skill/src/ui-ux-pro-max
python3 scripts/search.py "<产品描述 行业 关键词>" --design-system -p "项目名称" -f markdown
```

关键词越具体越好。例如 "dark magical portfolio AI agent alchemy mystical amber purple dark-mode" 比 "dark portfolio" 好得多。

输出中包含：Style、Colors（含 OKLCH 色值）、Typography（含 Google Fonts 导入链接）、Effects、Anti-patterns。

根据输出直接配置 `globals.css` 的 CSS 变量和 `layout.tsx` 的字体。

### Phase 1: 项目脚手架

```bash
npx create-next-app@latest <project-name> --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm
npm install framer-motion lucide-react @lobehub/icons @icons-pack/react-simple-icons
npx shadcn@latest init -d --force
npx shadcn@latest add @magicui/particles @magicui/typing-animation @magicui/bento-grid @magicui/magic-card @magicui/orbiting-circles @magicui/text-animate card badge separator input avatar --yes
```

WSL 注意：npm install 需要 `http_proxy='' https_proxy=''` 绕过本地代理。

### Phase 2: 并行写组件（推荐 delegate_task）

独立的多节页面适合用 `delegate_task` 并行构建所有 section 组件：

```json
{
  "tasks": [
    {"goal": "HeroSection: Particles + TypingAnimation + OrbitingCircles + scroll parallax"},
    {"goal": "CodexSection: BentoGrid skills grid with search + category filter"},
    {"goal": "TerminalSection: Interactive CLI emulator with command history"},
    {"goal": "ContactSection: MagicCard links + brand icons"},
    {"goal": "AtlasSection: SVG hub-and-spoke architecture diagram"}
  ]
}
```

一次性构建 5+ 个组件时，`delegate_task` 比逐一手写快 3-5 倍。需要给每个子任务提供：
1. 项目结构说明（路径约定、已安装的组件）
2. 设计系统色值（primary/accent/bg）
3. 每个组件的清晰 spec

子任务完成后，组合到 `page.tsx` 中。注意子任务生成的代码可能有细微风格差异，需统一修复。

### Phase 3: 构建验证

```bash
npm run build  # 无 TS 错误、无 lint 错误
```

### Phase 4: 部署到 GitHub Pages

1. **配置 next.config.ts**：
   ```ts
   const nextConfig: NextConfig = {
     output: "export",
     basePath: "/repo-name",  // 匹配 GitHub repo 名！
     images: { unoptimized: true },
   };
   ```

2. **启用 GitHub Pages（workflow 模式）**：
   ```bash
   # 创建仓库
   gh repo create owner/repo-name --public --source . --push
   
   # 切换到 GitHub Actions 构建源
   curl -X PUT -H "Authorization: token $(gh auth token)" \
     https://api.github.com/repos/owner/repo-name/pages \
     -d '{"build_type":"workflow"}'
   ```

3. **创建 deploy.yml**：
   ```yaml
   name: Deploy to GitHub Pages
   on: { push: { branches: ["main"] } }
   permissions: { contents: read, pages: write, id-token: write }
   jobs:
     deploy:
       runs-on: ubuntu-latest
       environment: { name: github-pages }
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-node@v4
         - run: npm ci && npm run build
         - uses: actions/upload-pages-artifact@v3
           with: { path: ./out }
         - uses: actions/deploy-pages@v4
   ```

4. **验证**：构建后检查 out/index.html 所有 href/src 路径是否带有 `/repo-name/` 前缀。

5. **GitHub Pages 域名格式**：`https://<user>.github.io/<repo-name>/`

## 已知陷阱

- **basePath 缺失 = 空白页面**：这是最常见的故障。资源路径不对，CSS/JS 全部 404，浏览器无任何报错，页面空白。始终在构建后检查路径前缀。
- **`bg-gradient-radial` 在 Tailwind v4 无效**：Tailwind v4 不识别这个类，静默忽略。用 `bg-[radial-gradient(...)]` 或 inline style 替代。
- **WSL npm 需要绕代理**：`http_proxy='' https_proxy='' npm install`
