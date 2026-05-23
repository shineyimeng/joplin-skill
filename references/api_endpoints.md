# Joplin REST API Endpoints Reference

## Base URL
`http://localhost:{port}` (default port: 41184, range: 41184-41194)

## Authentication
All requests require `?token=XXX` query parameter.

## Common Query Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `fields` | Comma-separated fields to return | `?fields=id,title,body` |
| `order_by` | Sort field | `?order_by=updated_time` |
| `order_dir` | Sort direction: ASC / DESC | `?order_dir=DESC` |
| `limit` | Items per page (max 100) | `?limit=50` |
| `page` | Page number (starts at 1) | `?page=2` |
| `token` | Auth token (required) | `?token=ABCD123...` |

## Paginated Response Format
```json
{
  "items": [...],
  "has_more": true
}
```

---

## Notes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notes` | List all notes. Params: `include_deleted=1`, `include_conflicts=1` |
| GET | `/notes/:id` | Get note by ID |
| GET | `/notes/:id/tags` | Get tags on a note |
| GET | `/notes/:id/resources` | Get resources attached to a note |
| POST | `/notes` | Create note. Body: `title`, `body` (Markdown) or `body_html` (HTML), `parent_id`, `image_data_url`, `is_todo`, `todo_due`, `todo_completed` |
| PUT | `/notes/:id` | Update note (partial) |
| DELETE | `/notes/:id` | Delete note. Params: `permanent=1` |
| DELETE | `/notes/:id/revisions` | Delete all revisions of a note |

### Note Key Properties
- `id`, `parent_id` (notebook), `title`, `body`, `body_html`
- `is_todo` (0/1), `todo_due`, `todo_completed` (timestamps)
- `source_url`, `latitude`, `longitude`, `altitude`
- `created_time`, `updated_time`, `user_created_time`, `user_updated_time`
- `is_shared`, `share_id`

---

## Folders (Notebooks)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/folders` | List all folders as tree (children in `children` key) |
| GET | `/folders/:id` | Get folder by ID |
| GET | `/folders/:id/notes` | List notes in a folder |
| POST | `/folders` | Create folder. Body: `title`, `parent_id` |
| PUT | `/folders/:id` | Update folder (partial) |
| DELETE | `/folders/:id` | Delete folder. Params: `permanent=1` |

### Folder Key Properties
- `id`, `title`, `parent_id`, `icon`
- `created_time`, `updated_time`
- `is_shared`, `share_id`

---

## Tags

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tags` | List all tags |
| GET | `/tags/:id` | Get tag by ID |
| GET | `/tags/:id/notes` | Get notes with this tag |
| POST | `/tags` | Create tag. Body: `title` |
| POST | `/tags/:id/notes` | Add tag to note. Body: `{"id": "note_id"}` |
| PUT | `/tags/:id` | Update tag |
| DELETE | `/tags/:id` | Delete tag |
| DELETE | `/tags/:id/notes/:note_id` | Remove tag from note |

---

## Resources (Attachments)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/resources` | List all resources |
| GET | `/resources/:id` | Get resource metadata |
| GET | `/resources/:id/file` | Download actual file |
| GET | `/resources/:id/notes` | Get notes using this resource |
| POST | `/resources` | Upload resource (multipart/form-data: `data` + `props`) |
| PUT | `/resources/:id` | Update resource (metadata or file) |
| DELETE | `/resources/:id` | Delete resource |

### Resource Upload Format
```
Content-Type: multipart/form-data
Field "data": file content
Field "props": JSON string, e.g. {"title": "my file"}
```

### Resource Key Properties
- `id`, `title`, `mime`, `filename`, `file_extension`, `size`
- `ocr_text`, `ocr_status`, `ocr_error`

---

## Revisions (History)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/revisions` | List all revisions |
| GET | `/revisions/:id` | Get revision |
| POST | `/revisions` | Create revision |
| PUT | `/revisions/:id` | Update revision |
| DELETE | `/revisions/:id` | Delete revision |

### Revision Key Properties
- `id`, `parent_id`, `item_type`, `item_id`
- `title_diff`, `body_diff`, `metadata_diff`

---

## Search

```
GET /search?query=YOUR_QUERY
```

Params:
- `query` (required): Search query using Joplin search syntax
- `type`: Filter by item type (note, folder, tag, resource). Uses simple case-insensitive match, not full-text.
- `fields`: Fields to return

Examples:
- `GET /search?query=python` — full-text search for "python"
- `GET /search?query=recipes&type=folder` — find folder named "recipes"
- `GET /search?query=project-*&type=tag` — find tags starting with "project-"

---

## Events (Change Tracking)

```
GET /events?cursor=XXX
```

- First call without cursor returns latest cursor only
- Subsequent calls with cursor return events since that cursor
- Events retained for 90 days
- Response includes `cursor` (for next call) and `has_more`

### Event Properties
- `id`, `item_type`, `item_id`, `type` (1=created, 2=updated, 3=deleted), `created_time`

---

## Ping

```
GET /ping → "JoplinClipperServer"
```

## Error Format
HTTP status ≥ 400, body: `{"error": "description"}`
