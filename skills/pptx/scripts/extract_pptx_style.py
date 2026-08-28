#!/usr/bin/env python3
"""Analyse a reference .pptx and synthesise a deck-wide design footprint.

Reads `ppt/theme/theme1.xml` (color scheme + font scheme) and the first
`ppt/slides/slide1.xml` (actual rPr usage) from the pptx zip. Produces:

    <output_dir>/global.css     — slide-canvas CSS using extracted variables
    <output_dir>/design.json    — palette + typography in slides_brief.json
                                  shape, plus the raw theme dump for audit

Usage:
    python extract_pptx_style.py <pptx_path> <output_dir>

The script imitates the pptx's palette / typography so downstream slide
generation can stay faithful to the reference deck. No external deps —
uses zipfile + xml.etree only.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

# Standard PowerPoint preset colors → hex. Used when a clrScheme slot points at
# a named preset rather than an explicit srgbClr.
PRESET_COLORS = {
    "windowText": "#000000", "windowBackground": "#FFFFFF",
    "menuText": "#000000", "menuBar": "#FFFFFF",
}


def _hex_from_node(node: ET.Element | None) -> str | None:
    if node is None:
        return None
    srgb = node.find("a:srgbClr", NS)
    if srgb is not None and srgb.get("val"):
        return "#" + srgb.get("val").upper()
    sys_ = node.find("a:sysClr", NS)
    if sys_ is not None:
        # sysClr always carries a lastClr fallback for the rendered hex.
        last = sys_.get("lastClr")
        if last:
            return "#" + last.upper()
        val = sys_.get("val")
        if val and val in PRESET_COLORS:
            return PRESET_COLORS[val]
    preset = node.find("a:prstClr", NS)
    if preset is not None and preset.get("val") in PRESET_COLORS:
        return PRESET_COLORS[preset.get("val")]
    return None


def parse_theme(theme_xml: bytes) -> dict:
    root = ET.fromstring(theme_xml)
    out: dict = {"palette": {}, "fonts": {"heading": None, "body": None}}

    clr = root.find(".//a:clrScheme", NS)
    if clr is not None:
        for slot in (
            "dk1", "lt1", "dk2", "lt2",
            "accent1", "accent2", "accent3", "accent4", "accent5", "accent6",
            "hlink", "folHlink",
        ):
            node = clr.find(f"a:{slot}", NS)
            hex_val = _hex_from_node(node)
            if hex_val:
                out["palette"][slot] = hex_val

    fonts = root.find(".//a:fontScheme", NS)
    if fonts is not None:
        major = fonts.find("a:majorFont/a:latin", NS)
        if major is not None and major.get("typeface"):
            out["fonts"]["heading"] = major.get("typeface")
        minor = fonts.find("a:minorFont/a:latin", NS)
        if minor is not None and minor.get("typeface"):
            out["fonts"]["body"] = minor.get("typeface")
        # East-asian fallback — useful when the deck is Chinese.
        major_ea = fonts.find("a:majorFont/a:ea", NS)
        if major_ea is not None and major_ea.get("typeface"):
            out["fonts"]["heading_ea"] = major_ea.get("typeface")
        minor_ea = fonts.find("a:minorFont/a:ea", NS)
        if minor_ea is not None and minor_ea.get("typeface"):
            out["fonts"]["body_ea"] = minor_ea.get("typeface")

    return out


def sample_slide_usage(slide_xml: bytes) -> dict:
    """Inspect actual srgbClr fills + rPr typefaces used on slide 1."""
    root = ET.fromstring(slide_xml)
    colors = collections.Counter()
    typefaces = collections.Counter()
    sizes = collections.Counter()
    for srgb in root.iter(f"{{{NS['a']}}}srgbClr"):
        if srgb.get("val"):
            colors["#" + srgb.get("val").upper()] += 1
    for rpr in root.iter(f"{{{NS['a']}}}rPr"):
        sz = rpr.get("sz")
        if sz:
            sizes[int(sz)] += 1
        for tag in ("latin", "ea", "cs"):
            face = rpr.find(f"a:{tag}", NS)
            if face is not None and face.get("typeface"):
                typefaces[face.get("typeface")] += 1
    return {
        "top_colors": colors.most_common(8),
        "top_typefaces": typefaces.most_common(6),
        "top_font_sizes_hpt": sizes.most_common(6),  # OOXML stores sz in hundredths of pt
    }


def synthesize_design(theme: dict, slide: dict | None) -> dict:
    p = theme["palette"]
    bg = p.get("lt1") or p.get("lt2") or "#FFFFFF"
    primary = p.get("dk1") or p.get("dk2") or "#1C1917"
    accent = p.get("accent1") or "#2563EB"

    # If slide1 uses a markedly more common non-bg, non-primary color, prefer
    # it as the accent — themes sometimes carry a placeholder accent that the
    # actual deck never uses.
    if slide:
        for hex_val, _count in slide["top_colors"]:
            if hex_val.upper() not in {bg.upper(), primary.upper()}:
                accent = hex_val
                break

    heading = theme["fonts"].get("heading") or "Inter"
    body = theme["fonts"].get("body") or heading
    return {
        "background": bg,
        "primary": primary,
        "accent": accent,
        "heading_font": heading,
        "body_font": body,
    }


CSS_TEMPLATE = """\
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Crimson+Text:wght@400;600;700&family=Noto+Sans+SC:wght@400;500;700&family=Noto+Serif+SC:wght@400;700&display=swap');

:root {{
  --bg: {bg};
  --primary: {primary};
  --accent: {accent};
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  font-family: '{body_font}', 'Inter', 'Helvetica Neue', 'Segoe UI', Arial,
               'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background-color: var(--bg);
  color: var(--primary);
}}

.slide {{
  width: 1280px;
  height: 720px;
  background-color: var(--bg);
  padding: 64px;
  position: relative;
  overflow: hidden;
}}

h1, h2, h3, .heading {{
  font-family: '{heading_font}', 'Crimson Text', 'Times New Roman', Georgia,
               'Noto Serif SC', 'Songti SC', 'SimSun', serif;
  color: var(--primary);
  line-height: 1.1;
}}

h1 {{ font-size: 88px; }}
h2 {{ font-size: 52px; }}
h3 {{ font-size: 32px; }}

p, li, td, .body-text {{
  font-family: '{body_font}', 'Inter', 'Helvetica Neue', Arial,
               'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 22px;
  line-height: 1.55;
  color: var(--primary);
}}

.accent-fg {{ color: var(--accent); }}
.accent-bg {{ background-color: var(--accent); color: var(--bg); }}
.accent-border {{ border: 4px solid var(--accent); }}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("pptx_path", type=Path)
    ap.add_argument("output_dir", type=Path)
    args = ap.parse_args()

    if not args.pptx_path.is_file() or args.pptx_path.suffix.lower() != ".pptx":
        print(f"error: {args.pptx_path} is not a .pptx file", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(args.pptx_path) as z:
        names = z.namelist()
        theme_files = sorted(n for n in names if re.match(r"ppt/theme/theme\d+\.xml$", n))
        if not theme_files:
            print("error: no ppt/theme/theme*.xml inside pptx", file=sys.stderr)
            return 1
        theme_xml = z.read(theme_files[0])
        slide_xml = None
        if "ppt/slides/slide1.xml" in names:
            slide_xml = z.read("ppt/slides/slide1.xml")

    theme = parse_theme(theme_xml)
    slide = sample_slide_usage(slide_xml) if slide_xml else None
    design = synthesize_design(theme, slide)

    css = CSS_TEMPLATE.format(
        bg=design["background"],
        primary=design["primary"],
        accent=design["accent"],
        heading_font=design["heading_font"],
        body_font=design["body_font"],
    )
    css_path = args.output_dir / "global.css"
    css_path.write_text(css, encoding="utf-8")

    design_payload = {
        "design": {
            "palette": {
                "background": design["background"],
                "primary": design["primary"],
                "accent": design["accent"],
            },
            "typography": {
                "heading": design["heading_font"],
                "body": design["body_font"],
            },
            "reference": f"imitating {args.pptx_path.name}",
        },
        "source_pptx": str(args.pptx_path.resolve()),
        "raw_theme": theme,
        "slide1_usage": slide,
    }
    design_path = args.output_dir / "design.json"
    design_path.write_text(json.dumps(design_payload, ensure_ascii=False, indent=2),
                           encoding="utf-8")

    print(f"wrote {css_path}")
    print(f"wrote {design_path}")
    print(f"palette: bg={design['background']} primary={design['primary']} accent={design['accent']}")
    print(f"fonts:  heading={design['heading_font']} body={design['body_font']}")
    if slide:
        print(f"slide1 top colors: {slide['top_colors'][:3]}")
        print(f"slide1 top typefaces: {slide['top_typefaces'][:3]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
