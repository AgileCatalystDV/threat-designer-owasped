"""Strip model thinking / redacted blocks from plain text (shared by asset/flows parsers)."""

from __future__ import annotations

import re

_LT, _GT = chr(60), chr(62)
_THINKING_BLOCK_PATTERNS = (
    re.compile(
        _LT + "redacted_thinking" + _GT + r".*?" + _LT + "/" + "redacted_thinking" + _GT,
        re.DOTALL | re.IGNORECASE,
    ),
    re.compile(
        _LT + "think" + _GT + r".*?" + _LT + "/" + "think" + _GT,
        re.DOTALL | re.IGNORECASE,
    ),
    re.compile(_LT + "/" + "redacted_thinking" + _GT, re.IGNORECASE),
)


def strip_thinking_markers(text: str) -> str:
    if not text or not isinstance(text, str):
        return text
    s = text
    for pat in _THINKING_BLOCK_PATTERNS:
        s = pat.sub("", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()
