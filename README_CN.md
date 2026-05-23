# 🗒️ Joplin Skill for OpenClaw

[English](./README.md) | 中文

一个将 [OpenClaw](https://github.com/nicepkg/openclaw) 代理连接到本地 [Joplin](https://joplinapp.org/) 笔记应用的技能。通过 Joplin REST API 实现笔记、笔记本和标签的完整 CRUD 操作，以及全文搜索、增量同步、网页剪藏和资源附件管理。

## 功能特性

- 📝 **笔记** — 创建、查看、更新、删除（支持 Markdown）
- 📂 **笔记本** — 层级目录管理，树形展示
- 🏷️ **标签** — 创建、分配、移除；按名称自动解析
- 🔍 **全文搜索** — 关键词、按类型筛选、通配符搜索
- 📎 **资源附件** — 上传文件、下载附件、生成 Markdown 引用链接
- 🌐 **网页剪藏** — 将任意 URL 剪藏为 Markdown 笔记（含来源链接）
- 🔄 **增量同步** — 基于事件驱动的变更检测，自动持久化游标
- 🤖 **名称自动解析** — 使用人类可读的名称替代 ID，操作更直观

## 前置条件

1. **Joplin 桌面端**运行中，且已启用 Web Clipper 服务
2. **授权 Token** — Joplin → 设置 → Web Clipper → 复制 Authorization Token

## 快速开始

### 1. 配置 Token

```bash
python scripts/joplin_api.py config --token YOUR_TOKEN
```

### 2. 自动检测连接

```bash
python scripts/joplin_api.py auto-detect
```

### 3. 验证连接

```bash
python scripts/joplin_api.py ping
```

配置保存在 `~/.qclaw/workspace/joplin_config.json`。

## 使用方法

### 笔记

```bash
# 列出笔记
python scripts/joplin_api.py list notes --folder "日记" --limit 20

# 创建笔记（笔记本和标签按名称自动解析）
python scripts/joplin_api.py create note --title "会议纪要" --body "Markdown 内容" --folder "工作" --tag "重要"

# 查看笔记详情
python scripts/joplin_api.py get note <ID> --fields id,title,body,updated_time

# 更新笔记
python scripts/joplin_api.py update note <ID> --title "新标题"

# 删除笔记
python scripts/joplin_api.py delete note <ID> --permanent
```

### 笔记本

```bash
python scripts/joplin_api.py list folders                              # 树形展示
python scripts/joplin_api.py create folder --title "项目"               # 顶级目录
python scripts/joplin_api.py create folder --title "2024" --parent_id <ID>  # 子目录
python scripts/joplin_api.py update folder <ID> --title "新名称"
python scripts/joplin_api.py delete folder <ID>
```

### 标签

```bash
python scripts/joplin_api.py list tags
python scripts/joplin_api.py create tag --title "待办"
python scripts/joplin_api.py add-tag <NOTE_ID> "待办"       # 自动解析/创建标签
python scripts/joplin_api.py remove-tag <TAG_ID> <NOTE_ID>
```

### 搜索

```bash
python scripts/joplin_search.py search "关键词"                     # 全文搜索
python scripts/joplin_search.py search "项目" --type folder         # 按类型搜索
python scripts/joplin_search.py search "会议-*" --type tag          # 通配符搜索
```

### 资源 / 附件

```bash
python scripts/joplin_resource.py upload /path/to/file.pdf --title "报告"
python scripts/joplin_resource.py download <RESOURCE_ID> --output ./report.pdf
python scripts/joplin_resource.py link <RESOURCE_ID>                 # Markdown 引用链接
python scripts/joplin_resource.py list --note <NOTE_ID>
```

### 网页剪藏

```bash
python scripts/joplin_clip.py clip https://example.com/article --folder "收藏" --tag "网页"
```

自动抓取网页 → 转 Markdown → 创建笔记（含 `source_url`）。

### 增量同步

```bash
python scripts/joplin_sync.py init           # 初始化游标
python scripts/joplin_sync.py pull           # 拉取上次以来的变更
python scripts/joplin_sync.py pull --full    # 全量拉取（首次同步）
```

返回变更事件（创建/更新/删除），游标自动持久化。

## 项目结构

```
joplin-skill/
├── SKILL.md                        # 技能定义与工作流指南
├── README.md                       # English README
├── README_CN.md                    # 中文 README
├── .gitignore
├── assets/
│   └── note_template.md            # 笔记模板（日记、会议、读书）
├── references/
│   ├── api_endpoints.md            # 完整 API 端点参考
│   └── item_types.md              # 数据类型与属性映射
└── scripts/
    ├── joplin_api.py               # 核心 API 封装与 CLI
    ├── joplin_clip.py              # 网页剪藏
    ├── joplin_resource.py          # 资源/附件管理
    ├── joplin_search.py            # 全文搜索
    └── joplin_sync.py              # 增量同步
```

## API 约定

| 约定 | 说明 |
|---|---|
| 时间戳 | 毫秒级 Unix 时间戳 |
| 布尔值 | 整数 `0` / `1` |
| 分页 | `limit`（最大 100）+ `page` + `has_more` |
| 字段过滤 | `--fields id,title,body` |
| 排序 | `--order_by updated_time --order_dir DESC` |
| 部分更新 | PUT 只修改传入的字段 |
| 软删除 | 默认行为；使用 `--permanent` 永久删除 |

## 名称自动解析

传入人类可读的名称，无需记忆 ID：

- `--folder "日记"` → 自动查找名为"日记"的笔记本 ID
- `add-tag <NOTE_ID> "重要"` → 自动查找或创建"重要"标签

## 错误处理

| HTTP 状态 | 含义 | 操作 |
|---|---|---|
| 连接失败 | Joplin 未运行或 Clipper 未启用 | 启动 Joplin 并启用 Web Clipper |
| 401 | Token 无效 | 重新运行 `config --token` |
| 404 | 项目不存在 | 检查 ID 是否正确 |

## 许可证

MIT
