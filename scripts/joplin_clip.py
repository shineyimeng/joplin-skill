#!/usr/bin/env python3
"""Joplin web clipper - fetch URL and save as note.

Usage:
    python joplin_clip.py clip <url> [--folder "Notebook"] [--tag "Tag"] [--format markdown|html]
"""

import argparse
import json
import os
import sys
import urllib.request
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from joplin_api import load_config, api_request, resolve_folder, resolve_tag


def fetch_url_content(url):
    """Fetch URL and extract title + body text."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; JoplinClipper/1.0)"
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    # Extract title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else url
    # Clean HTML entities
    title = re.sub(r"&amp;", "&", title)
    title = re.sub(r"&lt;", "<", title)
    title = re.sub(r"&gt;", ">", title)
    title = re.sub(r"&quot;", '"', title)
    title = re.sub(r"&#39;", "'", title)

    # Simple HTML to Markdown conversion
    body = html_to_markdown(html)

    return title, body


def html_to_markdown(html):
    """Simple HTML to Markdown conversion for common elements."""
    text = html

    # Remove script and style
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<nav[^>]*>.*?</nav>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<footer[^>]*>.*?</footer>", "", text, flags=re.IGNORECASE | re.DOTALL)

    # Headers
    for i in range(6, 0, -1):
        text = re.sub(rf"<h{i}[^>]*>(.*?)</h{i}>", "#" * i + r" \1\n\n", text, flags=re.IGNORECASE | re.DOTALL)

    # Paragraphs
    text = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", text, flags=re.IGNORECASE | re.DOTALL)

    # Bold / italic
    text = re.sub(r"<(strong|b)[^>]*>(.*?)</\1>", r"**\2**", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<(em|i)[^>]*>(.*?)</\1>", r"*\2*", text, flags=re.IGNORECASE | re.DOTALL)

    # Links
    text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.IGNORECASE | re.DOTALL)

    # Images
    text = re.sub(r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*/?\s*>', r"![\2](\1)", text, flags=re.IGNORECASE)
    text = re.sub(r'<img[^>]*src="([^"]*)"[^>]*/?\s*>', r"![](\1)", text, flags=re.IGNORECASE)

    # Lists
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"</?[uo]l[^>]*>", "\n", text, flags=re.IGNORECASE)

    # Line breaks
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<hr\s*/?>", "\n---\n", text, flags=re.IGNORECASE)

    # Code blocks
    text = re.sub(r"<pre[^>]*><code[^>]*>(.*?)</code></pre>", r"\n```\n\1\n```\n", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", text, flags=re.IGNORECASE | re.DOTALL)

    # Blockquotes
    text = re.sub(r"<blockquote[^>]*>(.*?)</blockquote>", lambda m: "> " + m.group(1).replace("\n", "\n> ") + "\n\n", text, flags=re.IGNORECASE | re.DOTALL)

    # Remove remaining tags
    text = re.sub(r"<[^>]+>", "", text)

    # Clean up HTML entities
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&#39;", "'", text)
    text = re.sub(r"&nbsp;", " ", text)

    # Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    return text.strip()


def cmd_clip(args, cfg):
    """Clip a URL and save as Joplin note."""
    token = cfg.get("token", "")
    if not token:
        print("Error: No token configured.", file=sys.stderr)
        sys.exit(1)

    port = cfg["port"]
    url = args.url

    print(f"Clipping: {url}", file=sys.stderr)

    # Fetch URL content
    try:
        title, body = fetch_url_content(url)
    except Exception as e:
        print(f"Failed to fetch URL: {e}", file=sys.stderr)
        sys.exit(1)

    # Build note data
    data = {
        "title": title,
        "source_url": url,
    }

    if args.format == "html":
        # Re-fetch raw HTML for body_html
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        data["body_html"] = html
        data["base_url"] = url.split("?")[0]
    else:
        data["body"] = body

    # Set notebook
    if args.folder:
        fid = resolve_folder(port, token, args.folder)
        if fid:
            data["parent_id"] = fid
        else:
            print(f"Warning: Folder '{args.folder}' not found. Using default notebook.", file=sys.stderr)
    elif cfg.get("default_folder"):
        data["parent_id"] = cfg["default_folder"]

    # Create note
    result = api_request("POST", "/notes", port, token, data=data)
    note_id = result.get("id")
    print(f"Note created: {note_id} - {title}", file=sys.stderr)

    # Add tag
    if args.tag and note_id:
        tag_id = resolve_tag(port, token, args.tag)
        if not tag_id:
            tag_result = api_request("POST", "/tags", port, token, data={"title": args.tag})
            tag_id = tag_result.get("id")
            print(f"Tag '{args.tag}' created.", file=sys.stderr)
        if tag_id:
            api_request("POST", f"/tags/{tag_id}/notes", port, token, data={"id": note_id})
            print(f"Tag '{args.tag}' added.", file=sys.stderr)

    print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    cfg = load_config()
    parser = argparse.ArgumentParser(description="Joplin web clipper")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("clip", help="Clip a URL to Joplin")
    p.add_argument("url", help="URL to clip")
    p.add_argument("--folder", default=None, help="Target notebook name or ID")
    p.add_argument("--tag", default=None, help="Tag to add (auto-created)")
    p.add_argument("--format", choices=["markdown", "html"], default="markdown",
                   help="Note format (default: markdown)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "clip":
        cmd_clip(args, cfg)


if __name__ == "__main__":
    main()
