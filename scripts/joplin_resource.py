#!/usr/bin/env python3
"""Joplin resource (attachment) management CLI.

Usage:
    python joplin_resource.py upload <file_path> [--title "Title"]
    python joplin_resource.py download <resource_id> --output <dir_or_path>
    python joplin_resource.py link <resource_id>       # Generate Markdown reference syntax
    python joplin_resource.py list [--note NOTE_ID]    # List resources
    python joplin_resource.py info <resource_id>       # Get resource metadata
"""

import argparse
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from joplin_api import load_config, api_request, paginate


def cmd_upload(args, cfg):
    """Upload a file as a Joplin resource."""
    token = cfg.get("token", "")
    if not token:
        print("Error: No token configured.", file=sys.stderr)
        sys.exit(1)

    port = cfg["port"]
    file_path = args.file_path

    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    title = args.title or filename
    props = json.dumps({"title": title})

    result = api_request(
        "POST", "/resources", port, token,
        files={"data": (filename, file_bytes), "props": props},
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"Resource uploaded: {result.get('id', 'N/A')}", file=sys.stderr)


def cmd_download(args, cfg):
    """Download a resource file."""
    token = cfg.get("token", "")
    if not token:
        print("Error: No token configured.", file=sys.stderr)
        sys.exit(1)

    port = cfg["port"]
    resource_id = args.resource_id
    output = args.output

    # Get resource metadata first for filename
    meta = api_request("GET", f"/resources/{resource_id}", port, token)
    filename = meta.get("filename", f"{resource_id}.bin")
    file_ext = meta.get("file_extension", "")
    if file_ext and not filename.endswith(f".{file_ext}"):
        filename = f"{filename}.{file_ext}"

    # Determine output path
    if os.path.isdir(output):
        output_path = os.path.join(output, filename)
    else:
        output_path = output

    # Download file content
    import urllib.request
    url = f"http://localhost:{port}/resources/{resource_id}/file?token={token}"
    try:
        urllib.request.urlretrieve(url, output_path)
        print(f"Downloaded to: {output_path}")
    except Exception as e:
        print(f"Download failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_link(args, cfg):
    """Generate Markdown reference syntax for a resource."""
    token = cfg.get("token", "")
    if not token:
        print("Error: No token configured.", file=sys.stderr)
        sys.exit(1)

    resource_id = args.resource_id
    meta = api_request("GET", f"/resources/{resource_id}", cfg["port"], token)
    title = meta.get("title", "resource")
    mime = meta.get("mime", "")

    if mime.startswith("image/"):
        # Image embed
        print(f"![{title}](:/{resource_id})")
    else:
        # File link
        print(f"[{title}](:/{resource_id})")


def cmd_list(args, cfg):
    """List resources, optionally filtered by note."""
    token = cfg.get("token", "")
    if not token:
        print("Error: No token configured.", file=sys.stderr)
        sys.exit(1)

    port = cfg["port"]
    if args.note:
        items = paginate(f"/notes/{args.note}/resources", port, token)
    else:
        items = paginate("/resources", port, token)

    print(json.dumps(items, indent=2, ensure_ascii=False))


def cmd_info(args, cfg):
    """Get resource metadata."""
    token = cfg.get("token", "")
    if not token:
        print("Error: No token configured.", file=sys.stderr)
        sys.exit(1)

    result = api_request("GET", f"/resources/{args.resource_id}", cfg["port"], token)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    cfg = load_config()
    parser = argparse.ArgumentParser(description="Joplin resource management")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("upload", help="Upload a file as resource")
    p.add_argument("file_path", help="Path to file to upload")
    p.add_argument("--title", default=None, help="Resource title (default: filename)")

    p = sub.add_parser("download", help="Download a resource file")
    p.add_argument("resource_id", help="Resource ID")
    p.add_argument("--output", required=True, help="Output directory or file path")

    p = sub.add_parser("link", help="Generate Markdown reference for a resource")
    p.add_argument("resource_id", help="Resource ID")

    p = sub.add_parser("list", help="List resources")
    p.add_argument("--note", default=None, help="Filter by note ID")

    p = sub.add_parser("info", help="Get resource metadata")
    p.add_argument("resource_id", help="Resource ID")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "upload": cmd_upload,
        "download": cmd_download,
        "link": cmd_link,
        "list": cmd_list,
        "info": cmd_info,
    }
    fn = dispatch.get(args.command)
    if fn:
        fn(args, cfg)


if __name__ == "__main__":
    main()
