# B站 412 反爬修复

## 问题

```bash
$ yt-dlp --dump-json "https://www.bilibili.com/video/BV1GJ411x7h7/"
ERROR: [BiliBili] 1GJ411x7h7: Unable to download JSON metadata:
  HTTP Error 412: Precondition Failed
```

## 修复

加 `Origin` 头即可：

```bash
yt-dlp --add-header "Origin:https://www.bilibili.com" \
       --add-header "Referer:https://www.bilibili.com/" \
       --dump-json "https://www.bilibili.com/video/BV1GJ411x7h7/"
```

来源：https://www.wholenotism.com/blog/2026/04/ytdlp-bilibili-error412.html

## 脚本中应用

脚本定义了 `BILI_HEADERS` 数组，所有 yt-dlp 调用统一引用：

```bash
BILI_HEADERS=(--add-header "Origin:https://www.bilibili.com" --add-header "Referer:https://www.bilibili.com/")
yt-dlp "${BILI_HEADERS[@]}" "${COOKIE_ARGS[@]}" --dump-json "$VIDEO_URL"
```
