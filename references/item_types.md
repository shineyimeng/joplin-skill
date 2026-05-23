# Joplin Item Types and Properties

## Item Type ID Mapping

| Name | ID | Description |
|------|----|-------------|
| note | 1 | Note |
| folder | 2 | Notebook (internally called "folder") |
| setting | 3 | Application setting |
| resource | 4 | File attachment |
| tag | 5 | Tag/label |
| note_tag | 6 | Note-Tag association |
| search | 7 | Saved search |
| alarm | 8 | Alarm/reminder |
| master_key | 9 | Encryption master key |
| item_change | 10 | Item change record |
| note_resource | 11 | Note-Resource association |
| resource_local_state | 12 | Resource local state |
| revision | 13 | Note revision/history |
| migration | 14 | Database migration |
| smart_filter | 15 | Smart filter |
| command | 16 | Command |

## Event Type IDs

| Value | Meaning |
|-------|---------|
| 1 | Created |
| 2 | Updated |
| 3 | Deleted |

## Data Type Conventions

- **Text**: UTF-8
- **Timestamps**: Unix timestamp in **milliseconds**
- **Booleans**: Integer `0` (false) or `1` (true)

## Note Properties (Complete)

| Property | Type | Description |
|----------|------|-------------|
| id | text | Unique identifier |
| parent_id | text | Notebook ID containing this note |
| title | text | Note title |
| body | text | Note body in Markdown |
| body_html | text | Note body in HTML (alternative to body) |
| base_url | text | Base URL for relative URLs in body_html |
| created_time | int | Creation timestamp (ms) |
| updated_time | int | Last update timestamp (ms) |
| user_created_time | int | User-set creation time |
| user_updated_time | int | User-set update time |
| is_conflict | int | Whether note is a conflict copy |
| is_todo | int | Whether note is a todo (0/1) |
| todo_due | int | Todo due date (ms timestamp) |
| todo_completed | int | Todo completion time (ms, 0=incomplete) |
| source_url | text | Source URL |
| source | text | Source type |
| source_application | text | Source application |
| application_data | text | Application-specific data |
| author | text | Note author |
| latitude | numeric | Geolocation latitude |
| longitude | numeric | Geolocation longitude |
| altitude | numeric | Geolocation altitude |
| order | numeric | Sort order within notebook |
| is_shared | int | Whether published (0/1) |
| share_id | text | Joplin Server share ID |
| conflict_original_id | text | Original note ID for conflict |
| master_key_id | text | Encryption master key ID |
| encryption_cipher_text | text | Encrypted content |
| encryption_applied | int | Whether encrypted (0/1) |
| markup_language | int | Markup language (1=Markdown) |
| image_data_url | text | Image to attach (Data URL format) |
| crop_rect | text | Crop rectangle: {x, y, width, height} |
| user_data | text | User-defined data |
| deleted_time | int | Deletion timestamp |

## Folder Properties (Complete)

| Property | Type | Description |
|----------|------|-------------|
| id | text | Unique identifier |
| title | text | Notebook title |
| parent_id | text | Parent notebook ID |
| icon | text | Custom icon |
| created_time | int | Creation timestamp (ms) |
| updated_time | int | Last update timestamp (ms) |
| user_created_time | int | User-set creation time |
| user_updated_time | int | User-set update time |
| is_shared | int | Whether published (0/1) |
| share_id | text | Joplin Server share ID |
| master_key_id | text | Encryption master key ID |
| encryption_cipher_text | text | Encrypted content |
| encryption_applied | int | Whether encrypted (0/1) |
| user_data | text | User-defined data |
| deleted_time | int | Deletion timestamp |

## Tag Properties (Complete)

| Property | Type | Description |
|----------|------|-------------|
| id | text | Unique identifier |
| title | text | Tag name |
| parent_id | text | Parent tag ID |
| created_time | int | Creation timestamp (ms) |
| updated_time | int | Last update timestamp (ms) |
| user_created_time | int | User-set creation time |
| user_updated_time | int | User-set update time |
| is_shared | int | Whether published (0/1) |
| encryption_cipher_text | text | Encrypted content |
| encryption_applied | int | Whether encrypted (0/1) |
| user_data | text | User-defined data |

## Resource Properties (Complete)

| Property | Type | Description |
|----------|------|-------------|
| id | text | Unique identifier |
| title | text | Resource title |
| mime | text | MIME type |
| filename | text | Original filename |
| file_extension | text | File extension |
| size | int | File size in bytes |
| created_time | int | Creation timestamp (ms) |
| updated_time | int | Last update timestamp (ms) |
| user_created_time | int | User-set creation time |
| user_updated_time | int | User-set update time |
| blob_updated_time | int | When file content was last updated |
| is_shared | int | Whether published (0/1) |
| share_id | text | Joplin Server share ID |
| master_key_id | text | Encryption master key ID |
| encryption_cipher_text | text | Encrypted content |
| encryption_applied | int | Whether encrypted (0/1) |
| encryption_blob_encrypted | int | Whether blob is encrypted (0/1) |
| user_data | text | User-defined data |
| ocr_text | text | OCR extracted text |
| ocr_details | text | OCR details |
| ocr_status | int | OCR processing status |
| ocr_error | text | OCR error message |
| ocr_driver_id | int | OCR driver identifier |
