"""
Extract ``ContinueThreatModeling``-shaped dicts from gap-analysis plain text.

Handles:

- XML ``<gap_analysis_report>`` / ``<decision>STOP|CONTINUE</decision>`` (see ``gap_prompt``)
- JSON objects with ``stop``, optional ``gap``, ``rating``

Stdlib only — no imports from ``state``.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from thinking_strip import strip_thinking_markers

_DECISION_RE = re.compile(
    r"<decision>\s*(STOP|CONTINUE)\s*</decision>",
    re.IGNORECASE | re.DOTALL,
)
_PRIORITY_ACTIONS_RE = re.compile(
    r"<priority_actions>(.*?)</priority_actions>",
    re.IGNORECASE | re.DOTALL,
)
_ACTION_RE = re.compile(
    r"<action\b[^>]*>(.*?)</action>",
    re.IGNORECASE | re.DOTALL,
)
_RATIONALE_RE = re.compile(
    r"<rationale>(.*?)</rationale>",
    re.IGNORECASE | re.DOTALL,
)
_RATING_RE = re.compile(
    r"<rating>\s*(\d+)\s*</rating>",
    re.IGNORECASE,
)


def _collapse_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def _parse_gap_analysis_xml(text: str) -> Optional[Dict[str, Any]]:
    m = _DECISION_RE.search(text)
    if not m:
        return None
    stop = m.group(1).upper() == "STOP"

    rating = 8 if stop else 5
    rm = _RATING_RE.search(text)
    if rm:
        rating = max(1, min(10, int(rm.group(1))))

    gap = ""
    if not stop:
        pa = _PRIORITY_ACTIONS_RE.search(text)
        if pa:
            inner = pa.group(1).strip()
            actions = _ACTION_RE.findall(inner)
            lines = [_collapse_ws(a) for a in actions if a.strip()]
            gap = "\n".join(f"- {line}" for line in lines)
        if not gap:
            rat = _RATIONALE_RE.search(text)
            if rat:
                gap = rat.group(1).strip()

    return {"stop": stop, "gap": "" if stop else gap, "rating": rating}


def _try_parse_continue_json(text: str) -> Optional[Dict[str, Any]]:
    """First JSON object with boolean ``stop`` (OpenAI-style args or raw JSON)."""
    decoder = json.JSONDecoder()
    pos = 0
    while True:
        i = text.find("{", pos)
        if i == -1:
            return None
        try:
            obj, _ = decoder.raw_decode(text[i:])
        except json.JSONDecodeError:
            pos = i + 1
            continue
        if isinstance(obj, dict) and "stop" in obj and isinstance(obj["stop"], bool):
            stop = bool(obj["stop"])
            raw_rating = obj.get("rating", 8 if stop else 5)
            try:
                rating = int(raw_rating)
            except (TypeError, ValueError):
                rating = 8 if stop else 5
            rating = max(1, min(10, rating))

            gap_val = obj.get("gap", "")
            if isinstance(gap_val, list):
                gap = "\n".join(str(x) for x in gap_val)
            else:
                gap = str(gap_val) if gap_val is not None else ""
            if stop:
                gap = ""
            return {"stop": stop, "gap": gap, "rating": rating}
        pos = i + 1


def extract_continue_dict_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse gap-analysis result into a dict for ``ContinueThreatModeling``.

    Returns ``None`` if nothing usable is found.
    """
    if not text or not text.strip():
        return None

    cleaned = strip_thinking_markers(text)
    if not cleaned.strip():
        return None

    xml = _parse_gap_analysis_xml(cleaned)
    if xml is not None:
        return xml

    return _try_parse_continue_json(cleaned)
