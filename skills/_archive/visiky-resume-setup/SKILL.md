---
name: visiky-resume-setup
category: productivity
description: 'Online resume generator by visiky (forked by user as `publieople/resume`). Configure resume data via resume.json and publish to GitHub so the online editor can preview. Covers schema mapping, repo requirements, URL query parameters, and deployment.'
tags:
  - resume
  - github-pages
  - visiky
  - career
trigger: |
  Use this skill when the user wants to:
  - Set up or update an online resume using the visiky/resume project
  - Debug why the online resume editor won't load their data
  - Migrate resume data from Notion/other sources to resume.json format
  - Publish their resume via the visiky/resume online editor
---

# visiky/resume 在线简历设置

## Project Overview

`visiky/resume` is a Gatsby-based online resume generator. The user's fork is at `publieople/resume`. The online editor is hosted at:

```
https://visiky.github.io/resume
```

## ⚠️ Critical: Data Source URL (most common pitfall)

The online editor fetches resume.json from this URL:

```
https://raw.githubusercontent.com/{user}/{user}/{branch}/resume.json
```

**Note:** Uses the same `{user}` for BOTH username and repo name. Requires a **special repository** named `{user}/{user}` (e.g., `publieople/publieople`), NOT the fork of the resume project (`publieople/resume`).

If the editor loads endlessly, check:
1. Does `publieople/publieople` repo exist? (Create it if not: `gh repo create username/username --public`)
2. Is `resume.json` present at `https://raw.githubusercontent.com/publieople/publieople/master/resume.json`?
3. Does it return 200?

## Resume Data Schema

The resume.json format:

```json
{
  "titleNameMap": {
    "educationList": "教育背景",
    "workExpList": "工作经历",
    "projectList": "项目经验",
    "skillList": "个人技能",
    "awardList": "更多信息",
    "workList": "个人作品",
    "aboutme": "个人评价"
  },
  "avatar": {
    "src": "",
    "hidden": true
  },
  "profile": {
    "name": "姓名",
    "email": "",
    "mobile": "手机号",
    "github": "https://github.com/username",
    "zhihu": "",
    "positionTitle": "求职意向（对应模板中的"职位"字段）",
    "workPlace": "期望工作地",
    "workExpYear": ""
  },
  "educationList": [
    {
      "edu_time": ["开始年份", "结束年份"],
      "school": "学校名",
      "major": "专业",
      "academic_degree": "学历"
    }
  ],
  "awardList": [
    {
      "award_info": "奖项名称 — 等级",
      "award_time": "年份"
    }
  ],
  "workExpList": [],
  "skillList": [
    {
      "skill_name": "技能类别",
      "skill_desc": "具体技能描述"
    }
  ],
  "projectList": [
    {
      "project_name": "项目名",
      "project_role": "角色",
      "project_time": "时间段",
      "project_desc": "简短描述",
      "project_content": "详细职责与成效"
    }
  ],
  "workList": [],
  "aboutme": {
    "aboutme_desc": "个人评价/自我介绍"
  },
  "theme": {
    "color": "#1677ff",
    "tagColor": "#52c41a"
  }
}
```

## Online Editor URL Parameters

| Param | Description | Example |
|-------|-------------|---------|
| `user` | GitHub username (required) | `publieople` |
| `branch` | Branch name (default: master) | `master` |
| `template` | template1, template2, template3 | `template2` |
| `mode` | `edit` for editor mode | `edit` |
| `lang` | Language (default: zh-CN) | `en-US` |

Full URL: `https://visiky.github.io/resume?user=publieople&branch=master`

## Resume from Notion Data

When extracting resume data from Notion:

1. Get the Notion page ID (e.g., `41ec7d67-f403-42f4-aa0c-f29a25298fe1`)
2. Use Notion API to fetch page blocks recursively (synced_block may contain the content)
3. Extract text from each block type (heading_1/2, paragraph, bulleted_list_item, divider, etc.)
4. Map sections to resume.json fields:
   - Profile fields → `profile`
   - 教育背景 → `educationList`
   - 核心技能 → `skillList`
   - 项目经历 → `projectList`
   - 社团经历 → `projectList` (same schema)
   - 竞赛奖项 → `awardList`
   - 兴趣/自我描述 → `aboutme.aboutme_desc`

## 🔍 Debugging Flow: Editor Doesn't Load / Spins Forever

When the editor shows a blank page or infinite spinner:

1. **Verify the raw URL**: Check `https://raw.githubusercontent.com/{user}/{user}/{branch}/resume.json` returns HTTP 200 (use curl).
2. **Check the fetch source**: The editor fetches from `https://raw.githubusercontent.com/${user}/${user}/${branch}/resume.json` (see `src/helpers/fetch-resume.ts` line 12). The `user` param is used for **both** username and repo name.
3. **Validate JSON locally**: `python3 -c "import json; json.load(open('resume.json')); print('Valid!')"`
4. **Check Chinese quotation marks** (see pitfall below)
5. **For import errors**: When the user downloads config and re-imports, the editor does `JSON.parse(reader.result)` (see `src/components/index.tsx` lines 177-202). Any JSON parse error shows "上传文件有误".

## ⚠️ Common Pitfall: Chinese Quotation Marks in JSON

Same as above — note that `"` (U+201C) and `"` (U+201D) get auto-converted to ASCII `"` by write tools.

**Fix**: Replace with CJK brackets `「」` before writing.

## 🏗️ Layout Balancing (Template 1)

Template 1 uses a CSS Grid layout, and the two columns display DIFFERENT sections, not the same content. Understanding this is critical for visual balance:

### Column Assignment

```
Left column  (basic-info, 2fr width):  Right column (main-info, 3fr width, gray bg):
──────────────────────────────────────────────────────────────────
1. Avatar (if not hidden)              1. workExpList  (工作经历)
2. Profile (name + contacts)           2. projectList  (项目经验)
3. Aboutme (aboutme_desc)
4. educationList  (教育背景)
5. workList  (个人作品)
6. skillList  (个人技能)
7. awardList  (更多信息/奖项)
```

### Why the Right Side Looks Sparse

The right column ONLY renders `workExpList` and `projectList`. If both are sparse or one is empty, the right side will visually look shorter/emptier than the left, which has 5-7 sections stacked.

### Balancing Strategies

| Symptom | Fix |
|---------|-----|
| Right side has less content volume | Expand `workExpList` entries with detailed `work_desc` (supports long text) |
| Right side has fewer sections than left | Put substantive experiences (lab work, blog operation, club leadership) into `workExpList` — the template labels it "工作经历" |
| Right side still looks empty | Add more `projectList` entries with detailed `project_desc` + `project_content` |
| Can't add more projects | Expand existing project descriptions — `project_content` renders as full paragraph text, adds visual weight |

### Key Insight

Think of the right column as "detailed experience" and the left as "summary/profile." The `workExpList` entries render with company name + department header and a full description paragraph, while `projectList` entries render with name, role tag, description, and content sections — both naturally add more vertical space than left-column items.

## ⚠️ Common Pitfall: Layout Imbalance

**Fix**: Before pushing, validate the JSON:

```bash
python3 -c "import json; json.load(open('resume.json')); print('Valid!')"
```

If it fails, replace with unambiguous alternatives (e.g., CJK brackets):

```python
content = content.replace('\u201c', '「').replace('\u201d', '」')
```

Then re-push to both repos (see Deployment below).

## Deployment

Method: Push resume.json to master branch of the special repo (`{user}/{user}`). The online editor reads directly from raw.githubusercontent.com — no build step needed.

**Preferred push method (avoids git push timeout):** Use the GitHub API directly:

```bash
gh api repos/{user}/{user}/contents/resume.json \
  -f content="$(base64 -w0 resume.json)" \
  -f message="update resume data" \
  -f branch=master \
  -f sha="$(gh api repos/{user}/{user}/contents/resume.json --jq '.sha')" \
  --method PUT
```

If the repo already has a resume.json, the `sha` parameter is required (points to the existing file blob). For the initial upload (no existing file), omit `-f sha=...`.

If using the `publieople/resume` fork, its GitHub Actions workflow (`deploy.yml`) auto-deploys to GitHub Pages on push to master, but this is for deploying the editor app itself, not the data.
