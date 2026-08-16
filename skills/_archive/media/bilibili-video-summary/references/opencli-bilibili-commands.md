# opencli bilibili Full Command Reference

Captured 2026-06-04 from `opencli bilibili -h`:

```
Usage: opencli bilibili <command> [args] [options]

Commands:
  comment <bvid> <message>    [write] Post comment/reply on video
  comments <bvid>             [read]  Get video comments (--parent <rpid> for replies)
  download <bvid>             [read]  Download video (requires yt-dlp)
  dynamic                     [read]  User dynamic feed
  favorite                    [write] Favorites
  feed [uid]                  [read]  Timeline (no uid=following, uid=user)
  feed-detail <id>            [read]  Dynamic detail (supports 充电 exclusive)
  following [uid]             [read]  Following list
  history                     [read]  Watch history
  hot                         [read]  Hot videos
  me                          [read]  My profile
  ranking                     [read]  Ranking board
  search <query>              [read]  Search videos or users
  subtitle <bvid>             [read]  Get video subtitles
  summary <bvid>              [read]  Official AI summary (章 outline + timestamps)
  user-videos <uid>           [read]  User's uploaded videos
  video <bvid>                [read]  Video metadata

Common options:
  -f, --format <fmt>  table, plain, json, yaml, md, csv (default: table)
  -h, --help          Display help

Browser options:
  --window <mode>     foreground or background
  --site-session      ephemeral or persistent
  --keep-tab          true or false
```
