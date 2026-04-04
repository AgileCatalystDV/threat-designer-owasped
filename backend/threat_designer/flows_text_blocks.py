"""
Extract FlowsList-shaped dicts from plain-text prompt output (<data_flow>, <trust_boundary>, threat table).

Matches `flow_prompt` / docs/qa/dataflowresonseqwen.md. Stdlib + regex only — no `state` import.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from thinking_strip import strip_thinking_markers

_DATA_FLOW_IGNORE = frozenset({"assets"})
_TRUST_IGNORE = frozenset({"boundary_type", "security_controls"})


def _parse_tagged_blocks(tag: str, text: str) -> List[str]:
    pat = re.compile(
        rf"<{re.escape(tag)}\s*>\s*(.*?)\s*</{re.escape(tag)}\s*>",
        re.IGNORECASE | re.DOTALL,
    )
    return [m.group(1).strip() for m in pat.finditer(text)]


def _parse_kv_block(block: str, *, ignore: frozenset) -> Dict[str, str]:
    """First `key: value` per line; key lowercased; ignores keys in ``ignore``."""
    out: Dict[str, str] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip().lower()
        val = val.strip()
        if key in ignore:
            continue
        out[key] = val
    return out


def _parse_threat_actor_table(text: str) -> List[Dict[str, str]]:
    """Markdown pipe table: Category | Description | Examples (→ ``example`` on ThreatSource)."""
    lines = text.splitlines()
    start: Optional[int] = None
    for i, line in enumerate(lines):
        low = line.lower()
        if (
            "|" in line
            and "category" in low
            and "description" in low
            and "example" in low
        ):
            start = i + 1
            break
    if start is None:
        return []
    while start < len(lines) and not lines[start].strip():
        start += 1
    if start < len(lines):
        sep = lines[start].strip()
        if sep and set(sep.replace("|", "").replace(" ", "")) <= {"-", ":"}:
            start += 1
    rows: List[Dict[str, str]] = []
    for line in lines[start:]:
        line = line.strip()
        if not line:
            continue
        if not line.startswith("|"):
            break
        if set(line.replace("|", "").replace(" ", "")) <= {"-", ":"}:
            continue
        inner = [p.strip() for p in line.split("|") if p.strip()]
        if len(inner) < 3:
            continue
        rows.append(
            {
                "category": inner[0],
                "description": inner[1],
                "example": inner[2],
            }
        )
    return rows


def extract_flows_dict_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse data_flow / trust_boundary XML blocks and threat markdown table.

    Returns dict with keys ``data_flows``, ``trust_boundaries``, ``threat_sources``
    (lists of plain dicts). ``None`` if nothing could be extracted.

    Extra prompt fields (``assets``, ``boundary_type``, …) are ignored so
    ``DataFlow`` / ``TrustBoundary`` Pydantic models stay unchanged.
    """
    if not text or not text.strip():
        return None

    cleaned = strip_thinking_markers(text)

    data_flows: List[Dict[str, str]] = []
    for inner in _parse_tagged_blocks("data_flow", cleaned):
        kv = _parse_kv_block(inner, ignore=_DATA_FLOW_IGNORE)
        req = ("flow_description", "source_entity", "target_entity")
        if all(k in kv for k in req):
            data_flows.append({k: kv[k] for k in req})

    trust_boundaries: List[Dict[str, str]] = []
    for inner in _parse_tagged_blocks("trust_boundary", cleaned):
        kv = _parse_kv_block(inner, ignore=_TRUST_IGNORE)
        req = ("purpose", "source_entity", "target_entity")
        if all(k in kv for k in req):
            trust_boundaries.append({k: kv[k] for k in req})

    threat_sources = _parse_threat_actor_table(cleaned)

    if not data_flows and not trust_boundaries and not threat_sources:
        return None

    return {
        "data_flows": data_flows,
        "trust_boundaries": trust_boundaries,
        "threat_sources": threat_sources,
    }
