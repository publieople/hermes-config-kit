# Notion Block 参考

完整 block 构造模板,供 `notionnext-blog` skill 调用。基础 7 个 helper 已在 SKILL.md 里,这里补充高级 block。

## 列表类

### Bulleted List Item
```python
{"object":"block","type":"bulleted_list_item",
 "bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":"..."}}]}}
```

### Numbered List Item
```python
{"object":"block","type":"numbered_list_item",
 "numbered_list_item":{"rich_text":[{"type":"text","text":{"content":"..."}}]}}
```

连续的 `numbered_list_item` 在 Notion 里会自动组成有序列表(从 1 开始)。

### To-Do
```python
{"object":"block","type":"to_do",
 "to_do":{"rich_text":[{"type":"text","text":{"content":"..."}}],
          "checked": False}}
```

## 富文本类

### Callout
```python
{"object":"block","type":"callout",
 "callout":{"icon":{"type":"emoji","emoji":"💡"},
            "rich_text":[{"type":"text","text":{"content":"..."}}],
            "color":"default"}}
```

color 可选: `default`/`gray`/`brown`/`orange`/`yellow`/`green`/`blue`/`purple`/`pink`/`red`,后缀 `_background` 是浅色背景。

### 行内富文本(同一 block 多种样式)
```python
{"object":"block","type":"paragraph",
 "paragraph":{"rich_text":[
   {"type":"text","text":{"content":"普通 "}},
   {"type":"text","text":{"content":"加粗"},"annotations":{"bold":True}},
   {"type":"text","text":{"content":" 代码 "},"annotations":{"code":True}},
   {"type":"text","text":{"content":" 链接"},"href":"https://example.com"},
   {"type":"text","text":{"content":" 颜色"},"annotations":{"color":"red"}},
 ]}}
```

annotations 支持: `bold` / `italic` / `strikethrough` / `underline` / `code` / `color`。

## 容器类

### Toggle(可折叠,单次请求最多 2 层嵌套)
```python
{"object":"block","type":"toggle",
 "toggle":{"rich_text":[{"type":"text","text":{"content":"点击展开"}}],
           "children":[/* 子 block */]}}
```

### Code
```python
{"object":"block","type":"code",
 "code":{"rich_text":[{"type":"text","text":{"content":"print('hi')"}}],
         "language":"python",
         "caption":[{"type":"text","text":{"content":"可选说明"}}]}}
```

**白名单关键值**: `plain text`, `bash`, `shell`, `powershell`, `python`, `javascript`, `typescript`, `json`, `yaml`, `html`, `css`, `markdown`, `sql`, `go`, `rust`, `java`, `c`, `c++`, `c#`, `ruby`, `php`, `mermaid`, `diff`, `dockerfile`, `makefile`, `xml`。**没有 `"text"`**。

### Quote / Divider / Equation
```python
{"object":"block","type":"quote",
 "quote":{"rich_text":[{"type":"text","text":{"content":"..."}}]}}

{"object":"block","type":"divider","divider":{}}

{"object":"block","type":"equation","equation":{"expression":"E = mc^2"}}
```

## 媒体类

### Image(外链)
```python
{"object":"block","type":"image",
 "image":{"type":"external",
          "external":{"url":"https://..."},
          "caption":[{"type":"text","text":{"content":"说明"}}]}}
```

### File(3 步)
1. `POST /v1/file_uploads` → upload_id
2. `POST /v1/file_uploads/{id}/send` multipart 上传
3. block 的 url 改为 `file:///upload_id`

### Bookmark / Embed
```python
{"object":"block","type":"bookmark",
 "bookmark":{"url":"https://...",
             "caption":[{"type":"text","text":{"content":"..."}}]}}
```

## 表格(table + table_row)

**两步建表:先建 table,table.children 必须是 table_row。**

```python
{"object":"block","type":"table",
 "table":{"table_width":3,
          "has_column_header":True,
          "has_row_header":False,
          "children":[
            {"object":"block","type":"table_row",
             "table_row":{"cells":[
               [{"type":"text","text":{"content":"列1"}}],
               [{"type":"text","text":{"content":"列2"}}],
               [{"type":"text","text":{"content":"列3"}}],
             ]}}
          ]}}
```

## 错误码速查

| 状态码 | 含义 | 常见原因 |
|--------|------|----------|
| 400 | 请求格式错 | code language 不在白名单 / position 字段位置错 / 必填字段缺 |
| 401 | 鉴权失败 | API key 错 / 被 shell 掩码成 `***` |
| 403 | 权限不足 | integration 未被加到 page/database 的 Connections |
| 404 | 找不到 | block_id / page_id 不存在或被删 |
| 429 | 限流 | 触发后等 `Retry-After` 秒 |
| 502/503 | Notion 挂了 | 几分钟后重试 |

## 限流

平均 3 req/s。批量请求间 `time.sleep(0.34)`,触发 429 后指数退避。

## 验证脚本模板

```python
import json, urllib.request

def fetch_all_children(block_id):
    out=[]; cursor=None
    while True:
        url=f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
        if cursor: url+=f"&start_cursor={cursor}"
        req=urllib.request.Request(url,headers={
            "Authorization":f"Bearer {key}","Notion-Version":"2022-06-28"})
        d=json.loads(urllib.request.urlopen(req).read())
        out.extend(d['results'])
        if not d.get('has_more'): break
        cursor=d['next_cursor']
    return out

# 找目标 H2 后面第一个 block
blocks = fetch_all_children(PAGE_ID)
h2_idx = next(i for i,b in enumerate(blocks)
              if b.get('type')=='heading_2'
              and '目标' in ''.join(r.get('plain_text','')
                  for r in b['heading_2']['rich_text']))
print("插入位置:", h2_idx, "下一个 block:", blocks[h2_idx+1].get('type'))
```

## NotionNext 上线验证

```python
import time
time.sleep(65)  # 等 NotionNext revalidate(默认 60s)
url = f"https://blog.for-people.cn/article/{page_id_no_dash}"
req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
body = urllib.request.urlopen(req).read().decode('utf-8','replace')
assert "你刚插入的关键字" in body, "未上线"
print("✅ 博客已更新")
```
