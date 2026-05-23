#!/usr/bin/env python3
"""Joplin search CLI - full-text and type-filtered search.

Usage:
    python joplin_search.py search "keyword" [--type note|folder|tag] [--limit 20] [--fields id,title]
    python joplin_search.py search "project-*" --type tag
    python joplin_search.py search "recipes" --type folder
"""

import argparse
import json
import os
import sys

# Reuse config loading from joplin_api
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from joplin_api import load_config, api_request, paginate


def cmd_search(args, cfg):
    """Search Joplin notes (or other item types)."""
    token = cfg.get("token", "")
    if not token:
        print("Error: No token configured. Run: python joplin_api.py config --token YOUR_TOKEN", file=sys.stderr)
        sys.exit(1)

    port = cfg["port"]
    query = args.query
    params = {"query": query}

    if args.type:
        params["type"] = args.type
    if args.fields:
        params["fields"] = args.fields
    if args.limit:
        params["limit"] = str(args.limit)

    # Search endpoint returns paginated results
    result = api_request("GET", "/search", port, token, params=params)
    items = result.get("items", [])

    # If has_more and no explicit limit, paginate
    if result.get("has_more") and not args.limit:
        page = 2
        while True:
            params["page"] = str(page)
            r = api_request("GET", "/search", port, token, params=params)
            items.extend(r.get("items", []))
            if not r.get("has_more"):
                break
            page += 1

    print(json.dumps(items, indent=2, ensure_ascii=False))

    if not items:
        print(f"No results for '{query}'.", file=sys.stderr)


def main():
    cfg = load_config()
    parser = argparse.ArgumentParser(description="Joplin search CLI")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("search", help="Search Joplin")
    p.add_argument("query", help="Search query (supports Joplin search syntax)")
    p.add_argument("--type", choices=["note", "folder", "tag", "resource"], default=None,
                   help="Filter by item type (uses simple matching, not full-text)")
    p.add_argument("--limit", type=int, default=None, help="Max results")
    p.add_argument("--fields", default=None, help="Comma-separated fields to return")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "search":
        cmd_search(args, cfg)


if __name__ == "__main__":
    main()
