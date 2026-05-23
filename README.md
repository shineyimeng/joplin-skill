# 🗒️ Joplin Skill for OpenClaw

A skill that connects [OpenClaw](https://github.com/nicepkg/openclaw) agents to the local [Joplin](https://joplinapp.org/) note-taking app via its REST API. Enables full CRUD operations on notes, notebooks, and tags, plus full-text search, incremental sync, web clipping, and resource/attachment management.

## Features

- 📝 **Notes** — Create, read, update, delete (with Markdown support)
- 📂 **Notebooks** — Hierarchical folder management with tree display
- 🏷️ **Tags** — Create, assign, remove; auto-resolve by name
- 🔍 **Full-text Search** — Keyword, type-filtered, and wildcard search
- 📎 **Resources** — Upload files, download attachments, generate Markdown links
- 🌐 **Web Clip** — Clip any URL to Markdown note (with source URL)
- 🔄 **Incremental Sync** — Event-driven change detection with cursor persistence
- 🤖 **Name Auto-Resolve** — Use human-readable names instead of IDs for folders and tags

## Prerequisites

1. **Joplin desktop** running with Web Clipper service enabled
2. **Authorization token** from Joplin → Settings → Web Clipper → Copy Authorization Token

## Quick Start

### 1. Configure the token

```bash
python scripts/joplin_api.py config --token YOUR_TOKEN
```

### 2. Auto-detect connection

```bash
python scripts/joplin_api.py auto-detect
```

### 3. Verify connection

```bash
python scripts/joplin_api.py ping
```

Configuration is saved to `~/.qclaw/workspace/joplin_config.json`.

## Usage

### Notes

```bash
# List notes
python scripts/joplin_api.py list notes --folder "Diary" --limit 20

# Create a note (folder/tag auto-resolved by name)
python scripts/joplin_api.py create note --title "Meeting Notes" --body "Markdown content" --folder "Work" --tag "Important"

# Get note details
python scripts/joplin_api.py get note <ID> --fields id,title,body,updated_time

# Update a note
python scripts/joplin_api.py update note <ID> --title "New Title"

# Delete a note
python scripts/joplin_api.py delete note <ID> --permanent
```

### Notebooks

```bash
python scripts/joplin_api.py list folders                              # Tree view
python scripts/joplin_api.py create folder --title "Projects"          # Top-level
python scripts/joplin_api.py create folder --title "2024" --parent_id <ID>  # Sub-folder
python scripts/joplin_api.py update folder <ID> --title "Renamed"
python scripts/joplin_api.py delete folder <ID>
```

### Tags

```bash
python scripts/joplin_api.py list tags
python scripts/joplin_api.py create tag --title "TODO"
python scripts/joplin_api.py add-tag <NOTE_ID> "TODO"      # Auto-resolve/create
python scripts/joplin_api.py remove-tag <TAG_ID> <NOTE_ID>
```

### Search

```bash
python scripts/joplin_search.py search "keyword"                    # Full-text
python scripts/joplin_search.py search "project" --type folder      # By type
python scripts/joplin_search.py search "meeting-*" --type tag       # Wildcard
```

### Resources / Attachments

```bash
python scripts/joplin_resource.py upload /path/to/file.pdf --title "Report"
python scripts/joplin_resource.py download <RESOURCE_ID> --output ./report.pdf
python scripts/joplin_resource.py link <RESOURCE_ID>                # Markdown link
python scripts/joplin_resource.py list --note <NOTE_ID>
```

### Web Clip

```bash
python scripts/joplin_clip.py clip https://example.com/article --folder "Bookmarks" --tag "web"
```

Fetches the page, converts to Markdown, and creates a note with `source_url`.

### Incremental Sync

```bash
python scripts/joplin_sync.py init           # Initialize cursor
python scripts/joplin_sync.py pull           # Pull changes since last sync
python scripts/joplin_sync.py pull --full    # Full pull (first-time sync)
```

Returns change events (create/update/delete); cursor is persisted automatically.

## Project Structure

```
joplin-skill/
├── SKILL.md                        # Skill definition & workflow guide
├── README.md                       # This file
├── .gitignore
├── assets/
│   └── note_template.md            # Note templates (diary, meeting, reading)
├── references/
│   ├── api_endpoints.md            # Full API endpoint reference
│   └── item_types.md              # Data types & property mapping
└── scripts/
    ├── joplin_api.py               # Core API wrapper & CLI
    ├── joplin_clip.py              # Web clipper
    ├── joplin_resource.py          # Resource/attachment management
    ├── joplin_search.py            # Full-text search
    └── joplin_sync.py              # Incremental sync
```

## API Conventions

| Convention | Detail |
|---|---|
| Timestamps | Millisecond Unix timestamps |
| Booleans | Integer `0` / `1` |
| Pagination | `limit` (max 100) + `page` + `has_more` |
| Field filter | `--fields id,title,body` |
| Sort | `--order_by updated_time --order_dir DESC` |
| Partial update | PUT only modifies passed fields |
| Soft delete | Default; use `--permanent` for hard delete |

## Name Auto-Resolution

Pass human-readable names instead of IDs:

- `--folder "日记"` → automatically resolves to the notebook ID
- `add-tag <NOTE_ID> "重要"` → automatically finds or creates the tag

## Error Handling

| HTTP Status | Meaning | Action |
|---|---|---|
| Connection failed | Joplin not running or Clipper disabled | Start Joplin & enable Web Clipper |
| 401 | Invalid token | Re-run `config --token` |
| 404 | Item not found | Check the ID |

## License

MIT
