"""
Parse OpenAI-style tool JSON from plain text (Gemma / LM Studio without tool_calls).

Handles ``{"name": "AssetsList", "arguments": {...}}`` and direct ``{...}`` payloads.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional


def repair_json_llm_typos(s: str) -> str:
    """Fix common model typos that break ``json.loads``."""
    t = s.replace('"、name"', '"name"')
    return t


def _strip_markdown_fence(text: str) -> str:
    t = text.strip()
    if not t.startswith("```"):
        return t
    lines = t.split("\n")
    if not lines:
        return t
    if lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def try_parse_json_object(text: str) -> Optional[Dict[str, Any]]:
    if not text or not str(text).strip():
        return None
    t = _strip_markdown_fence(str(text))
    t = repair_json_llm_typos(t)
    try:
        out = json.loads(t)
    except json.JSONDecodeError:
        return None
    return out if isinstance(out, dict) else None


def tool_arguments_if_name(
    data: Dict[str, Any], expected_name: str
) -> Optional[Dict[str, Any]]:
    if data.get("name") != expected_name:
        return None
    args = data.get("arguments")
    return args if isinstance(args, dict) else None
