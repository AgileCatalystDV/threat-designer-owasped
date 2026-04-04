"""
Extract threat rows from plain-text / pseudo-tool-call output (Qwen-style ``<parameter=threats>`` JSON).

Supports:

- Multiple ``<parameter=threats>`` blocks (merged, deduplicated by ``name``).
- Truncated JSON arrays: all **complete** threat objects before the cut are kept.
- Full-array parse when the fragment is valid JSON (fast path).

Stdlib + ``json.JSONDecoder`` only — no imports from ``state`` (keeps unit tests lightweight).
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Optional

from thinking_strip import strip_thinking_markers

_PARAMETER_THREATS = re.compile(
    r"<parameter\s*=\s*threats\s*>",
    re.IGNORECASE,
)
_PARAMETER_CLOSE = re.compile(r"</parameter\s*>", re.IGNORECASE)


def _looks_like_threat_row(d: Dict[str, Any]) -> bool:
    return bool(
        isinstance(d, dict)
        and {"name", "stride_category", "description", "target"}.issubset(d.keys())
    )


def merge_threat_rows_by_name(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge rows in document order: first time a ``name`` appears defines position;
    later duplicates replace the row (last wins on content).
    """
    seen: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for row in rows:
        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        key = name.strip()
        if key not in seen:
            order.append(key)
        seen[key] = row
    return [seen[k] for k in order]


def _iter_complete_threat_objects_in_array(array_fragment: str) -> List[Dict[str, Any]]:
    """
    Decode every **complete** JSON object at the top level of an array fragment.

    ``array_fragment`` must start with ``[`` (after optional whitespace). Stops at
    first incomplete object (truncated stream / invalid tail).
    """
    s = array_fragment.lstrip()
    if not s.startswith("["):
        return []
    decoder = json.JSONDecoder()
    i = 1
    n = len(s)
    out: List[Dict[str, Any]] = []
    while i < n:
        while i < n and s[i] in " \t\n\r,":
            i += 1
        if i >= n:
            break
        if s[i] != "{":
            break
        try:
            obj, end = decoder.raw_decode(s[i:])
        except json.JSONDecodeError:
            break
        if isinstance(obj, dict) and _looks_like_threat_row(obj):
            out.append(obj)
        i = i + end
    return out


def _extract_threats_from_parameter_segment(segment: str) -> List[Dict[str, Any]]:
    """Content after ``<parameter=threats>`` until ``</parameter>`` or end."""
    seg = segment.strip()
    close = _PARAMETER_CLOSE.search(seg)
    if close:
        seg = seg[: close.start()].strip()

    i = seg.find("[")
    if i == -1:
        return []

    tail = seg[i:]
    decoder = json.JSONDecoder()
    try:
        obj, _ = decoder.raw_decode(tail)
        if isinstance(obj, list) and obj and all(isinstance(x, dict) for x in obj):
            if _looks_like_threat_row(obj[0]):
                return list(obj)
    except json.JSONDecodeError:
        pass

    return _iter_complete_threat_objects_in_array(tail)


def _try_decode_threat_array(decoder: json.JSONDecoder, segment: str) -> Optional[List[Dict[str, Any]]]:
    """Scan ``segment`` for JSON arrays; return first list of threat-shaped dicts (full parse)."""
    pos = 0
    while True:
        i = segment.find("[", pos)
        if i == -1:
            return None
        try:
            obj, _ = decoder.raw_decode(segment[i:])
            if isinstance(obj, list) and obj and all(isinstance(x, dict) for x in obj):
                if _looks_like_threat_row(obj[0]):
                    return list(obj)
        except json.JSONDecodeError:
            pass
        pos = i + 1


def _try_decode_threats_wrapped_object(decoder: json.JSONDecoder, text: str) -> Optional[List[Dict[str, Any]]]:
    """Parse ``{\"threats\": [...]}`` if present (tool-args-shaped text)."""
    pos = 0
    while True:
        i = text.find("{", pos)
        if i == -1:
            return None
        try:
            obj, _ = decoder.raw_decode(text[i:])
            if isinstance(obj, dict) and "threats" in obj:
                t = obj["threats"]
                if isinstance(t, list) and t and all(isinstance(x, dict) for x in t):
                    if _looks_like_threat_row(t[0]):
                        return list(t)
        except json.JSONDecodeError:
            pass
        pos = i + 1


def extract_threat_dicts_from_text(text: str) -> Optional[List[Dict[str, Any]]]:
    """
    Parse threat dicts from Qwen-style ``<parameter=threats>`` blocks (possibly
    truncated), ``{\"threats\": [...]}``, or a top-level ``[...]`` array.

    Multiple ``<parameter=threats>`` segments are merged; duplicate ``name`` values
    collapse with **last occurrence winning** (stable order by first seen name).
    """
    if not text or not text.strip():
        return None

    cleaned = strip_thinking_markers(text)
    if not cleaned.strip():
        return None

    decoder = json.JSONDecoder()
    merged: List[Dict[str, Any]] = []

    for m in _PARAMETER_THREATS.finditer(cleaned):
        seg = cleaned[m.end() :]
        part = _extract_threats_from_parameter_segment(seg)
        if part:
            merged.extend(part)

    if merged:
        out = merge_threat_rows_by_name(merged)
        return out if out else None

    found = _try_decode_threats_wrapped_object(decoder, cleaned)
    if found is not None:
        return found

    full = _try_decode_threat_array(decoder, cleaned)
    if full is not None:
        return full

    i = cleaned.find("[")
    if i != -1:
        partial = _iter_complete_threat_objects_in_array(cleaned[i:])
        if partial:
            return merge_threat_rows_by_name(partial)

    return None
