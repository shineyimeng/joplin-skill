#!/usr/bin/env python3
"""Joplin REST API core wrapper.

Provides unified CLI access to the Joplin Data API (notes, folders, tags, etc.)
Requires Joplin desktop with Web Clipper service enabled.

Usage:
    python joplin_api.py ping
    python joplin_api.py list notes [--folder ID] [--fields id,title] [--limit 100]
    python joplin_api.py list folders
    python joplin_api.py list tags
    python joplin_api.py list resources
    python joplin_api.py get note <id> [--fields id,title,body]
    python joplin_api.py get folder <id>
    python joplin_api.py get tag <id>
    python joplin_api.py create note --title "Title" --body "Markdown" [--folder ID|NAME] [--tag TAG]
    python joplin_api.py create folder --title "Name" [--parent_id ID]
    python joplin_api.py create tag --title "Name"
    python joplin_api.py update note <id> [--title "New"] [--body "New"] [--parent_id ID]
    python joplin_api.py update folder <id> [--title "New"]
    python joplin_api.py delete note <id> [--permanent]
    python joplin_api.py delete folder <id> [--permanent]
    python joplin_api.py delete tag <id>
    python joplin_api.py add-tag <note_id> <tag_id_or_name>
    python joplin_api.py remove-tag <tag_id> <note_id>
    python joplin_api.py resolve folder "Notebook Name"
    python joplin_api.py resolve tag "Tag Name"
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CONFIG_PATH = os.path.join(
    os.environ.get("USERPROFILE", os.environ.get("HOME", ".")),
    ".qclaw", "workspace", "joplin_config.json",
)

DEFAULT_PORT = 41184
PORT_RANGE = range(41184, 41195)


def load_config():
    """Load config from JSON file, returning defaults if missing."""
    cfg = {"port": DEFAULT_PORT, "token": "", "default_folder": "", "sync_cursor": ""}
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    return cfg


def save_config(cfg):
    """Persist config to JSON file."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _base_url(port):
    return f"http://localhost:{port}"


def api_request(method, path, port, token, data=None, params=None, files=None):
    """Make an API request and return parsed JSON (or raw string for /ping).

    Args:
        method: GET / POST / PUT / DELETE
        path:   e.g. "/notes"
        port:   port number
        token:  auth token
        data:   dict body (JSON)
        params: dict query params (token is added automatically)
        files:  dict for multipart upload {"data": (filename, bytes), "props": json_str}
    """
    q = dict(params or {})
    if token:
        q["token"] = token
    qs = urllib.parse.urlencode(q, doseq=True)
    url = f"{_base_url(port)}{path}?{qs}"

    if files:
        # multipart/form-data for resource upload
        boundary = "----JoplinBoundary7MA4YWxkTrZu0gW"
        body_parts = []
        for key, val in files.items():
            if key == "data":
                filename, file_bytes = val
                body_parts.append(
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="data"; filename="{filename}"\r\n'
                    f"Content-Type: application/octet-stream\r\n\r\n".encode("utf-8")
                    + file_bytes
                    + b"\r\n"
                )
            else:
                body_parts.append(
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
                    f"{val}\r\n".encode("utf-8")
                )
        body_parts.append(f"--{boundary}--\r\n".encode("utf-8"))
        body = b"".join(body_parts)
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
    else:
        headers = {}
        body = None
        if data is not None:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            if path == "/ping":
                return raw.strip()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(err_body)
            print(f"API Error {e.code}: {err_json.get('error', err_body)}", file=sys.stderr)
        except json.JSONDecodeError:
            print(f"API Error {e.code}: {err_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection Error: {e.reason}", file=sys.stderr)
        print("Is Joplin running with Web Clipper enabled?", file=sys.stderr)
        sys.exit(1)


def paginate(path, port, token, params=None, limit=100):
    """Fetch all pages of a paginated endpoint."""
    all_items = []
    page = 1
    p = dict(params or {})
    p["limit"] = limit
    while True:
        p["page"] = page
        result = api_request("GET", path, port, token, params=p)
        items = result.get("items", [])
        all_items.extend(items)
        if not result.get("has_more", False):
            break
        page += 1
    return all_items


# ---------------------------------------------------------------------------
# Auto-resolve helpers
# ---------------------------------------------------------------------------

def resolve_folder(port, token, name):
    """Resolve a folder/notebook name to its ID. Returns ID or None."""
    folders = paginate("/folders", port, token)
    for f in folders:
        if f.get("title", "").lower() == name.lower():
            return f["id"]
        # also check children
        for child in f.get("children", []):
            if child.get("title", "").lower() == name.lower():
                return child["id"]
    return None


def resolve_tag(port, token, name):
    """Resolve a tag name to its ID. Returns ID or None."""
    tags = paginate("/tags", port, token)
    for t in tags:
        if t.get("title", "").lower() == name.lower():
            return t["id"]
    return None


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

def cmd_ping(args, cfg):
    """Test if Joplin API is reachable."""
    port = args.port or cfg["port"]
    result = api_request("GET", "/ping", port, "")
    if result == "JoplinClipperServer":
        print(f"OK - Joplin API running on port {port}")
    else:
        print(f"Unexpected response: {result}")
        sys.exit(1)


def cmd_list(args, cfg):
    """List resources."""
    token = cfg.get("token", "")
    if not token:
        print("Error: No token configured. Run: python joplin_api.py config --token YOUR_TOKEN", file=sys.stderr)
        sys.exit(1)

    port = cfg["port"]
    resource = args.resource  # notes / folders / tags / resources
    endpoint_map = {
        "notes": "/notes",
        "folders": "/folders",
        "tags": "/tags",
        "resources": "/resources",
    }
    endpoint = endpoint_map.get(resource)
    if not endpoint:
        print(f"Unknown resource type: {resource}", file=sys.stderr)
        sys.exit(1)

    params = {}
    if args.fields:
        params["fields"] = args.fields
    if args.order_by:
        params["order_by"] = args.order_by
    if args.order_dir:
        params["order_dir"] = args.order_dir

    # Special: notes in a folder
    if resource == "notes" and args.folder:
        folder_id = args.folder
        # Try resolve by name
        if not folder_id.isalnum():
            resolved = resolve_folder(port, token, folder_id)
            if resolved:
                folder_id = resolved
            else:
                print(f"Folder '{args.folder}' not found.", file=sys.stderr)
                sys.exit(1)
        endpoint = f"/folders/{folder_id}/notes"

    if args.limit and args.limit <= 100:
        params["limit"] = args.limit
        params["page"] = 1
        result = api_request("GET", endpoint, port, token, params=params)
        items = result.get("items", [])
    else:
        items = paginate(endpoint, port, token, params=params)

    print(json.dumps(items, indent=2, ensure_ascii=False))


def cmd_get(args, cfg):
    """Get a single resource by ID."""
    token = cfg.get("token", "")
    if not token:
        print("Error: No token configured.", file=sys.stderr)
        sys.exit(1)

    resource = args.resource
    item_id = args.id
    endpoint_map = {
        "note": "/notes",
        "folder": "/folders",
        "tag": "/tags",
        "resource": "/resources",
    }
    base = endpoint_map.get(resource)
    if not base:
        print(f"Unknown resource type: {resource}", file=sys.stderr)
        sys.exit(1)

    params = {}
    if args.fields:
        params["fields"] = args.fields

    result = api_request("GET", f"{base}/{item_id}", cfg["port"], token, params=params)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_create(args, cfg):
    """Create a new resource."""
    token = cfg.get("token", "")
    if not token:
        print("Error: No token configured.", file=sys.stderr)
        sys.exit(1)

    port = cfg["port"]
    resource = args.resource

    if resource == "note":
        data = {"title": args.title or "Untitled"}
        if args.body:
            data["body"] = args.body
        if args.parent_id:
            data["parent_id"] = args.parent_id
        elif args.folder:
            # Resolve folder name to ID
            fid = resolve_folder(port, token, args.folder)
            if fid:
                data["parent_id"] = fid
            else:
                print(f"Warning: Folder '{args.folder}' not found. Note will go to default notebook.", file=sys.stderr)
        elif cfg.get("default_folder"):
            data["parent_id"] = cfg["default_folder"]

        result = api_request("POST", "/notes", port, token, data=data)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # Add tag if specified
        if args.tag and result.get("id"):
            tag_id = resolve_tag(port, token, args.tag)
            if not tag_id:
                # Create the tag first
                tag_result = api_request("POST", "/tags", port, token, data={"title": args.tag})
                tag_id = tag_result.get("id")
            if tag_id:
                api_request("POST", f"/tags/{tag_id}/notes", port, token, data={"id": result["id"]})
                print(f"Tag '{args.tag}' added.", file=sys.stderr)

    elif resource == "folder":
        data = {"title": args.title or "New Folder"}
        if args.parent_id:
            data["parent_id"] = args.parent_id
        result = api_request("POST", "/folders", port, token, data=data)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif resource == "tag":
        data = {"title": args.title or "New Tag"}
        result = api_request("POST", "/tags", port, token, data=data)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print(f"Cannot create resource type: {resource}", file=sys.stderr)
        sys.exit(1)


def cmd_update(args, cfg):
    """Update a resource."""
    token = cfg.get("token", "")
    if not token:
        print("Error: No token configured.", file=sys.stderr)
        sys.exit(1)

    port = cfg["port"]
    resource = args.resource
    item_id = args.id

    endpoint_map = {
        "note": "/notes",
        "folder": "/folders",
        "tag": "/tags",
        "resource": "/resources",
    }
    base = endpoint_map.get(resource)
    if not base:
        print(f"Unknown resource type: {resource}", file=sys.stderr)
        sys.exit(1)

    data = {}
    if args.title:
        data["title"] = args.title
    if args.body:
        data["body"] = args.body
    if args.parent_id:
        data["parent_id"] = args.parent_id

    if not data:
        print("Nothing to update. Provide --title, --body, or --parent_id.", file=sys.stderr)
        sys.exit(1)

    result = api_request("PUT", f"{base}/{item_id}", port, token, data=data)
    print(json.dumps(result, indent=2, ensure_ascii=False) if result else '{"status":"ok"}')


def cmd_delete(args, cfg):
    """Delete a resource."""
    token = cfg.get("token", "")
    if not token:
        print("Error: No token configured.", file=sys.stderr)
        sys.exit(1)

    resource = args.resource
    item_id = args.id

    endpoint_map = {
        "note": "/notes",
        "folder": "/folders",
        "tag": "/tags",
        "resource": "/resources",
    }
    base = endpoint_map.get(resource)
    if not base:
        print(f"Unknown resource type: {resource}", file=sys.stderr)
        sys.exit(1)

    params = {}
    if args.permanent:
        params["permanent"] = "1"

    result = api_request("DELETE", f"{base}/{item_id}", cfg["port"], token, params=params)
    print("Deleted." if not result else json.dumps(result, indent=2, ensure_ascii=False))


def cmd_add_tag(args, cfg):
    """Add a tag to a note."""
    token = cfg.get("token", "")
    if not token:
        print("Error: No token configured.", file=sys.stderr)
        sys.exit(1)

    port = cfg["port"]
    note_id = args.note_id
    tag_input = args.tag_id

    # Resolve tag name to ID
    if not tag_input.isalnum() or len(tag_input) != 32:
        tag_id = resolve_tag(port, token, tag_input)
        if not tag_id:
            # Create the tag
            tag_result = api_request("POST", "/tags", port, token, data={"title": tag_input})
            tag_id = tag_result.get("id")
            if not tag_id:
                print(f"Failed to create tag '{tag_input}'.", file=sys.stderr)
                sys.exit(1)
            print(f"Tag '{tag_input}' created (id: {tag_id}).", file=sys.stderr)
    else:
        tag_id = tag_input

    api_request("POST", f"/tags/{tag_id}/notes", port, token, data={"id": note_id})
    print(f"Tag added to note {note_id}.")


def cmd_remove_tag(args, cfg):
    """Remove a tag from a note."""
    token = cfg.get("token", "")
    if not token:
        print("Error: No token configured.", file=sys.stderr)
        sys.exit(1)

    tag_id = args.tag_id
    note_id = args.note_id
    api_request("DELETE", f"/tags/{tag_id}/notes/{note_id}", cfg["port"], token)
    print(f"Tag {tag_id} removed from note {note_id}.")


def cmd_resolve(args, cfg):
    """Resolve a name to an ID."""
    token = cfg.get("token", "")
    if not token:
        print("Error: No token configured.", file=sys.stderr)
        sys.exit(1)

    port = cfg["port"]
    resource = args.resource
    name = args.name

    if resource == "folder":
        rid = resolve_folder(port, token, name)
    elif resource == "tag":
        rid = resolve_tag(port, token, name)
    else:
        print(f"Cannot resolve type: {resource}", file=sys.stderr)
        sys.exit(1)

    if rid:
        print(rid)
    else:
        print(f"{resource} '{name}' not found.", file=sys.stderr)
        sys.exit(1)


def cmd_config(args, cfg):
    """Set or view config values."""
    if args.token:
        cfg["token"] = args.token
    if args.port:
        cfg["port"] = args.port
    if args.default_folder:
        cfg["default_folder"] = args.default_folder

    if args.token or args.port or args.default_folder:
        save_config(cfg)
        print(f"Config saved to {CONFIG_PATH}")

    print(json.dumps(cfg, indent=2, ensure_ascii=False))


def cmd_auto_detect(args, cfg):
    """Auto-detect the Joplin API port by scanning port range."""
    for port in PORT_RANGE:
        try:
            result = api_request("GET", "/ping", port, "")
            if result == "JoplinClipperServer":
                cfg["port"] = port
                save_config(cfg)
                print(f"Found Joplin on port {port}. Config updated.")
                return
        except Exception:
            continue
    print("Joplin API not found on ports 41184-41194.", file=sys.stderr)
    print("Make sure Joplin is running and Web Clipper is enabled.", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Argparse setup
# ---------------------------------------------------------------------------

def main():
    cfg = load_config()

    parser = argparse.ArgumentParser(
        description="Joplin REST API CLI wrapper",
        prog="joplin_api",
    )
    sub = parser.add_subparsers(dest="command")

    # ping
    p = sub.add_parser("ping", help="Test API connection")
    p.add_argument("--port", type=int, default=None)

    # auto-detect
    sub.add_parser("auto-detect", help="Auto-detect Joplin port")

    # config
    p = sub.add_parser("config", help="View or set config")
    p.add_argument("--token", default=None)
    p.add_argument("--port", type=int, default=None)
    p.add_argument("--default_folder", default=None)

    # list
    p = sub.add_parser("list", help="List resources")
    p.add_argument("resource", choices=["notes", "folders", "tags", "resources"])
    p.add_argument("--folder", default=None, help="Filter notes by folder (ID or name)")
    p.add_argument("--fields", default=None, help="Comma-separated fields to return")
    p.add_argument("--order_by", default=None)
    p.add_argument("--order_dir", choices=["ASC", "DESC"], default=None)
    p.add_argument("--limit", type=int, default=None)

    # get
    p = sub.add_parser("get", help="Get a single resource")
    p.add_argument("resource", choices=["note", "folder", "tag", "resource"])
    p.add_argument("id", help="Item ID")
    p.add_argument("--fields", default=None)

    # create
    p = sub.add_parser("create", help="Create a resource")
    p.add_argument("resource", choices=["note", "folder", "tag"])
    p.add_argument("--title", default=None)
    p.add_argument("--body", default=None)
    p.add_argument("--folder", default=None, help="Notebook name or ID (notes only)")
    p.add_argument("--parent_id", default=None, help="Parent folder ID")
    p.add_argument("--tag", default=None, help="Tag to add (notes only, auto-created)")

    # update
    p = sub.add_parser("update", help="Update a resource")
    p.add_argument("resource", choices=["note", "folder", "tag"])
    p.add_argument("id", help="Item ID")
    p.add_argument("--title", default=None)
    p.add_argument("--body", default=None)
    p.add_argument("--parent_id", default=None)

    # delete
    p = sub.add_parser("delete", help="Delete a resource")
    p.add_argument("resource", choices=["note", "folder", "tag", "resource"])
    p.add_argument("id", help="Item ID")
    p.add_argument("--permanent", action="store_true", help="Permanently delete (skip trash)")

    # add-tag / remove-tag
    p = sub.add_parser("add-tag", help="Add tag to note")
    p.add_argument("note_id")
    p.add_argument("tag_id", help="Tag ID or name (auto-created)")

    p = sub.add_parser("remove-tag", help="Remove tag from note")
    p.add_argument("tag_id")
    p.add_argument("note_id")

    # resolve
    p = sub.add_parser("resolve", help="Resolve a name to ID")
    p.add_argument("resource", choices=["folder", "tag"])
    p.add_argument("name")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "ping": cmd_ping,
        "auto-detect": cmd_auto_detect,
        "config": cmd_config,
        "list": cmd_list,
        "get": cmd_get,
        "create": cmd_create,
        "update": cmd_update,
        "delete": cmd_delete,
        "add-tag": cmd_add_tag,
        "remove-tag": cmd_remove_tag,
        "resolve": cmd_resolve,
    }
    fn = dispatch.get(args.command)
    if fn:
        fn(args, cfg)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
