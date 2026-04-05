"""
Extract payload between [TOOL_REQUEST] and [END_TOOL_REQUEST] for plain-text fallbacks.

When present, leading text before [TOOL_REQUEST] is discarded (not parsed).
If markers are missing or incomplete, the original string is returned unchanged
so existing Qwen/text parsers keep working.
"""

from __future__ import annotations

from typing import Optional

MARKER_START = "[TOOL_REQUEST]"
MARKER_END = "[END_TOOL_REQUEST]"


def extract_inner_payload(text: str) -> Optional[str]:
    """
    Return content strictly between MARKER_START and MARKER_END, stripped.

    Returns None if ``text`` is falsy, if MARKER_START is absent, or if
    MARKER_END does not appear after MARKER_START.
    """
    if not text or not isinstance(text, str):
        return None
    i = text.find(MARKER_START)
    if i < 0:
        return None
    after_start = text[i + len(MARKER_START) :]
    j = after_start.find(MARKER_END)
    if j < 0:
        return None
    inner = after_start[:j].strip()
    return inner


def normalize_text_for_structured_fallback(text: str) -> str:
    """
    If ``[TOOL_REQUEST]`` … ``[END_TOOL_REQUEST]`` wraps a payload, return only
    that inner segment (prefix and suffix discarded). Otherwise return ``text``
    unchanged.
    """
    inner = extract_inner_payload(text)
    if inner is not None:
        return inner
    return text
