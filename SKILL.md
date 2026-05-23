---
name: joplin
description: |
  连接本地 Joplin 笔记应用，操作笔记、笔记本、标签和资源。支持 CRUD、全文搜索、增量同步和网页剪藏。
  当用户提到 Joplin、Joplin笔记、笔记本管理、Joplin标签、剪藏到Joplin、搜索Joplin笔记、Joplin同步、
  笔记创建/查找/更新/删除时触发。
---

# Joplin Skill

## 前置条件

1. Joplin 桌面端运行中
2. Web Clipper 服务已启用（Joplin → 设置 → Web Clipper → 启用服务）
3. 需要认证 token（Joplin → Web Clipper Options → 复制 Authorization Token）

## 首次连接

1. 配置 token：
   ```
   python "{SKILL_DIR}/scripts/joplin_api.py" config --token YOUR_TOKEN
   ```
2. 检测连接（自动发现端口）：
   ```
   python "{SKILL_DIR}/scripts/joplin_api.py" auto-detect
   ```
3. 验证连接：
   ```
   python "{SKILL_DIR}/scripts/joplin_api.py" ping
   ```

配置保存在 `~/.qclaw/workspace/joplin_config.json`，包含 port、token、default_folder、sync_cursor。

## 工作流

### 笔记操作

**列出笔记**：
```
python "{SKILL_DIR}/scripts/joplin_api.py" list notes [--folder "笔记本名"] [--fields id,title,updated_time] [--limit 50]
```

**获取笔记详情**：
```
python "{SKILL_DIR}/scripts/joplin_api.py" get note <ID> [--fields id,title,body]
```

**创建笔记**（--folder 按名称自动解析，--tag 自动创建）：
```
python "{SKILL_DIR}/scripts/joplin_api.py" create note --title "标题" --body "Markdown内容" --folder "日记" --tag "重要"
```

**更新笔记**（部分更新，未传属性不变）：
```
python "{SKILL_DIR}/scripts/joplin_api.py" update note <ID> --title "新标题"
python "{SKILL_DIR}/scripts/joplin_api.py" update note <ID> --parent_id <目标笔记本ID>  # 移动笔记
```

**删除笔记**：
```
python "{SKILL_DIR}/scripts/joplin_api.py" delete note <ID> [--permanent]
```

### 笔记本操作

```
python "{SKILL_DIR}/scripts/joplin_api.py" list folders          # 树形结构
python "{SKILL_DIR}/scripts/joplin_api.py" create folder --title "新笔记本" [--parent_id ID]
python "{SKILL_DIR}/scripts/joplin_api.py" update folder <ID> --title "新名"
python "{SKILL_DIR}/scripts/joplin_api.py" delete folder <ID>
```

### 标签操作

```
python "{SKILL_DIR}/scripts/joplin_api.py" list tags
python "{SKILL_DIR}/scripts/joplin_api.py" create tag --title "新标签"
python "{SKILL_DIR}/scripts/joplin_api.py" add-tag <NOTE_ID> "标签名"    # 按名自动解析/创建
python "{SKILL_DIR}/scripts/joplin_api.py" remove-tag <TAG_ID> <NOTE_ID>
```

### 搜索

```
python "{SKILL_DIR}/scripts/joplin_search.py" search "关键词"              # 全文搜索
python "{SKILL_DIR}/scripts/joplin_search.py" search "项目" --type folder  # 按类型搜索
python "{SKILL_DIR}/scripts/joplin_search.py" search "project-*" --type tag  # 通配符搜索
```

### 资源/附件

```
python "{SKILL_DIR}/scripts/joplin_resource.py" upload <FILE_PATH> [--title "标题"]
python "{SKILL_DIR}/scripts/joplin_resource.py" download <RESOURCE_ID> --output <PATH>
python "{SKILL_DIR}/scripts/joplin_resource.py" link <RESOURCE_ID>       # 生成 Markdown 引用
python "{SKILL_DIR}/scripts/joplin_resource.py" list [--note <NOTE_ID>]
```

### 网页剪藏

```
python "{SKILL_DIR}/scripts/joplin_clip.py" clip <URL> --folder "收藏" --tag "网页"
```
自动抓取网页 → 转 Markdown → 创建笔记（含 source_url）。

### 增量同步

```
python "{SKILL_DIR}/scripts/joplin_sync.py" init                    # 首次初始化 cursor
python "{SKILL_DIR}/scripts/joplin_sync.py" pull                    # 拉取自上次以来的变更
python "{SKILL_DIR}/scripts/joplin_sync.py" pull --full             # 全量拉取（首次同步）
```
返回事件列表（创建/更新/删除），cursor 自动持久化。

## API 通用规则

- 时间戳：毫秒级 Unix 时间戳
- 布尔值：整数 0/1
- 分页：limit(最大100) + page + has_more
- 字段过滤：`--fields id,title,body`
- 排序：`--order_by updated_time --order_dir DESC`
- PUT 部分更新：未传属性保持不变
- 默认删除移入回收站，`--permanent` 永久删除

## 名称自动解析

`--folder` 和 `add-tag` 参数支持按名称传值，脚本自动查找对应 ID：
- `--folder "日记"` → 自动查找名为"日记"的笔记本 ID
- `add-tag <NOTE_ID> "重要"` → 自动查找/创建"重要"标签

## 笔记模板

笔记模板在 `assets/note_template.md`，支持日记、会议纪要、读书笔记。
使用时读取模板，替换 `{变量}` 后作为 --body 传入。

## 端点与属性详细参考

需要查看完整端点列表或属性详情时，按需加载：
- **端点参考**：`references/api_endpoints.md`
- **类型映射与属性**：`references/item_types.md`

## 错误处理

HTTP ≥ 400 返回 `{"error": "描述"}`，脚本自动解析并输出友好提示。
常见错误：
- 连接失败 → 检查 Joplin 是否运行 + Web Clipper 是否启用
- 401 → token 无效，重新配置
- 404 → ID 不存在
