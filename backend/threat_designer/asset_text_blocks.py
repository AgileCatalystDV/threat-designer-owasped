"""
Extract asset rows from plain-text prompt output (Type/Name/Description/Criticality).

Stdlib + regex only — no imports from `state` (keeps unit tests lightweight).
Used by `asset_text_parser.py`.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from thinking_strip import strip_thinking_markers

_ASSET_BLOCK_RE = re.compile(
    r"Type:\s*(Asset|Entity)\s*\n"
    r"\s*Name:\s*([^\n]+?)\s*\n"
    r"\s*Description:\s*((?:.|\n)+?)(?=\n\s*Criticality:\s*(?:Low|Medium|High)\b)"
    r"\s*\n\s*Criticality:\s*(Low|Medium|High)\b",
    re.IGNORECASE | re.MULTILINE,
)


def extract_asset_dicts_from_text(text: str) -> Optional[List[Dict[str, Any]]]:
    """
    Parse prompt-style blocks into dicts suitable for `Assets` / `AssetsList`.

    Returns None if no blocks match.
    """
    if not text or not text.strip():
        return None

    cleaned = strip_thinking_markers(text)
    rows: List[Dict[str, Any]] = []

    for m in _ASSET_BLOCK_RE.finditer(cleaned):
        raw_type = m.group(1).strip().title()
        if raw_type not in ("Asset", "Entity"):
            continue
        name = m.group(2).strip()
        description = m.group(3).strip()
        crit_raw = m.group(4).strip().title()
        if crit_raw not in ("Low", "Medium", "High"):
            continue
        rows.append(
            {
                "type": raw_type,
                "name": name,
                "description": description,
                "criticality": crit_raw,
            }
        )

    return rows if rows else None
