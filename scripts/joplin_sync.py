#!/usr/bin/env python3
"""Joplin incremental sync based on Events API.

Usage:
    python joplin_sync.py init                      # Get current cursor (no history)
    python joplin_sync.py pull [--cursor CURSOR]    # Pull changes since cursor
    python joplin_sync.py pull --full               # Full pull (first sync)
"""

import argparse
import json
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from joplin_api import load_config, save_config, api_request


EVENT_TYPE_MAP = {1: "created", 2: "updated", 3: "deleted"}
ITEM_TYPE_MAP = {
    1: "note", 2: "folder", 3: "setting", 4: "resource", 5: "tag",
    6: "note_tag", 7: "search", 8: "alarm", 9: "master_key",
    10: "item_change", 11: "note_resource", 12: "resource_local_state",
    13: "revision", 14: "migration", 15: "smart_filter", 16: "command",
}


def cmd_init(args, cfg):
    """Initialize sync by getting the latest cursor (no historical events)."""
    token = cfg.get("token", "")
    if not token:
        print("Error: No token configured.", file=sys.stderr)
        sys.exit(1)

    result = api_request("GET", "/events", cfg["port"], token)
    cursor = result.get("cursor", "")
    if cursor:
        cfg["sync_cursor"] = cursor
        save_config(cfg)
        print(f"Sync initialized. Cursor: {cursor}")
        print("No historical events fetched. Use 'pull' to get future changes.")
    else:
        print("Could not get cursor. Make sure Joplin API is accessible.", file=sys.stderr)
        sys.exit(1)


def cmd_pull(args, cfg):
    """Pull events since the given cursor (or stored cursor, or full)."""
    token = cfg.get("token", "")
    if not token:
        print("Error: No token configured.", file=sys.stderr)
        sys.exit(1)

    port = cfg["port"]

    if args.full:
        cursor = ""
    else:
        cursor = args.cursor or cfg.get("sync_cursor", "")
        if not cursor:
            print("No cursor available. Run 'init' first or use --full.", file=sys.stderr)
            sys.exit(1)

    all_events = []
    params = {}
    if cursor:
        params["cursor"] = cursor

    while True:
        result = api_request("GET", "/events", port, token, params=params)
        events = result.get("items", [])
        all_events.extend(events)

        if not result.get("has_more", False):
            break

        # Update cursor for next page
        new_cursor = result.get("cursor", "")
        if new_cursor:
            params["cursor"] = new_cursor
        else:
            break

    # Get final cursor
    final_cursor = ""
    if all_events:
        # The cursor from the last response
        last_result = api_request("GET", "/events", port, token, params={"cursor": params.get("cursor", "")} if not params.get("cursor") else params)
        final_cursor = last_result.get("cursor", "")

    # Save cursor
    if final_cursor:
        cfg["sync_cursor"] = final_cursor
        save_config(cfg)

    # Format output
    formatted_events = []
    for ev in all_events:
        formatted_events.append({
            "id": ev.get("id"),
            "type": EVENT_TYPE_MAP.get(ev.get("type"), ev.get("type")),
            "item_type": ITEM_TYPE_MAP.get(ev.get("item_type"), ev.get("item_type")),
            "item_id": ev.get("item_id"),
            "created_time": ev.get("created_time"),
        })

    output = {
        "cursor": final_cursor,
        "count": len(formatted_events),
        "events": formatted_events,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def main():
    cfg = load_config()
    parser = argparse.ArgumentParser(description="Joplin incremental sync")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="Initialize sync cursor")

    p = sub.add_parser("pull", help="Pull changes since cursor")
    p.add_argument("--cursor", default=None, help="Cursor to start from (default: stored cursor)")
    p.add_argument("--full", action="store_true", help="Full pull (all available events)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {"init": cmd_init, "pull": cmd_pull}
    fn = dispatch.get(args.command)
    if fn:
        fn(args, cfg)


if __name__ == "__main__":
    main()
