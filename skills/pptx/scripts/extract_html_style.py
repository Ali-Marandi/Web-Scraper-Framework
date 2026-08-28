#!/usr/bin/env python3
"""Extract every <style>...</style> block from a reference HTML and write the
concatenated CSS to <output_dir>/global.css.

Usage:
    python extract_html_style.py <html_path> <output_dir> [--name FILE]

The output file name defaults to global.css so it slots straight into the
ppt skill's `<work_dir>/slides/global.css` convention. Pass --name to override.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

STYLE_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)


def extract_style_blocks(html_text: str) -> list[str]:
    return [m.group(1) for m in STYLE_RE.finditer(html_text)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("html_path", type=Path, help="path to source HTML file")
    ap.add_argument("output_dir", type=Path, help="directory to write the CSS into")
    ap.add_argument("--name", default="global.css",
                    help="output CSS file name (default: global.css)")
    args = ap.parse_args()

    if not args.html_path.is_file():
        print(f"error: {args.html_path} is not a file", file=sys.stderr)
        return 2

    text = args.html_path.read_text(encoding="utf-8", errors="replace")
    blocks = extract_style_blocks(text)
    if not blocks:
        print(f"error: no <style> blocks found in {args.html_path}", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    css = "\n\n".join(b.strip() for b in blocks)
    out = args.output_dir / args.name
    out.write_text(css, encoding="utf-8")
    print(f"wrote {out} ({len(css)} bytes from {len(blocks)} <style> block(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
