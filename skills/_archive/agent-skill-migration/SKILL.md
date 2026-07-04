---
name: agent-skill-migration
description: 从其他 Agent 的迁移包文档创建本地 Skill — 配置适配、API 发现、规则映射、脚本生成
---

# agent-skill-migration — Agent 技能迁移工作流

将其他 Agent（如拉琪奥）导出的迁移包文档转换为本地可用的 Skill + 可执行脚本。

## 触发条件

用户发送迁移包文档（Markdown/文本），包含：
- "迁移包"、"打包时间"、"来源 Agent" 等关键词
- "你说下一个X的skill并配置好" — 指示性要求
- 包含数据库 ID、API Key 路径、业务分类规则等配置信息
- 描述了一套完整的 Agent 操作流程（记账、管理、查询等）

## 工作流程

### Phase 1：阅读与识别

1. 读完整迁移文档，提取关键信息：
   - 第三方服务（Notion API, 飞书 API, 数据库等）
   - 认证方式（API Key 路径、格式）
   - 关键资源 ID（database_id, sheet_id 等）
   - 业务规则（分类体系、验证规则、特殊场景）

2. 检查本地是否有对应的基础 Skill（如 `notion`）：
   - `skills_list` 搜服务名
   - 用 `skill_view` 确认覆盖的 API 能力

### Phase 2：配置与适配

3. 安装/检查认证凭据：
   - `~/.config/<service>/api_key` 是否存在
   - 如果不存在，要求用户提供

4. 验证凭据连通性：
   ```bash
   NOTION_KEY=$(cat ~/.config/notion/api_key)
   curl -s -X POST "https://api.notion.com/v1/search" \
     -H "Authorization: Bearer $NOTION_KEY" \
     -H "Notion-Version: 2025-09-03" \
     -H "Content-Type: application/json" \
     -d '{"query":""}'
   ```

5. **文档 ID ≠ 实际 ID**：迁移包中的数据库/资源 ID 来自另一个 workspace。
   - 用 search/query API 发现用户的实际资源
   - 通过搜索名称为用户找到匹配的数据库
   - 用元数据 API 验证字段结构是否匹配迁移文档

### Phase 3：验证数据库结构

6. 查询数据库元数据确认字段兼容性：
   - `GET /v1/data_sources/{data_source_id}`（Notion 2025-09-03 API）
   - 对比迁移文档的字段名、选项列表
   - 记录 data_source_id 和 database_id 的映射差异

7. 识别关键差异并记录：
   - `database_id`（创建页面用）vs `data_source_id`（查询用）— Notion 2025-09-03 有此区分
   - 选项数量差异（如迁移包写 20 大项，实际 16 项 → 以实际为准）

### Phase 4：创建 Skill

8. 用 `skill_manage(action='create')` 创建领域技能：
   - SKILL.md：完整业务规则 + API 要点 + ⚠️ 铁律
   - 包含：数据库配置表、分类规则、特殊场景、退款流程、API 模板

9. 编写可执行 Python 脚本（放入 `scripts/`）：
   - **安全创建脚本**（推荐）：
     - 选项验证：创建前查数据库元数据，验证所有 select/multi_select
     - 幂等检查：搜索是否有重复记录
     - 审核模式：`--review` 参数，展示计划后用户确认
     - 自动化：时间标签推断、默认值填充
   - **查询脚本**：
     - 优先用 data_source/query 端点（精确查数据库，不混入其他页面）
     - 支持 `--limit`, `--search`, `--month` 筛选
     - 格式化输出（图标、金额、分类对齐）

10. 用 `chmod +x` 赋予执行权限

### Phase 5：测试

11. 测试查询脚本 -> 验证数据库连接和数据格式
12. 修复查询端点选择（search 端点会混入 workspace 所有页面）

### 铁律（迁移时注意）

- **不可直接使用迁移包中的资源 ID** — 必须通过 API 发现用户的实际资源
- **选项验证** 必须查数据库元数据，不能从已有记录推断
- **审核模式** 是安全底线，所有写操作必须先展示再执行
- Notion 2025-09-03 API 有 `database_id`（创建页面/relation）和 `data_source_id`（查询）的区分
- 脚本中的字段名（如"项目""金额"）必须精准匹配数据库的实际字段名

## Pitfalls

- **WebP 图片**：用户常发截图，当前模型可能不支持图片。考虑 tesseract OCR 或安装 PIL。
- **sudo 不可用**：依赖包用 `pip install --user` 或 uv 工具链安装
- **search API 混页**：`POST /v1/search` 返回 workspace 所有 page，非目标数据库的记录也会混入。精确查询用 `/v1/data_sources/{id}/query`。
