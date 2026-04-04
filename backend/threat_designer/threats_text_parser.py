"""
Build ``ThreatsList`` from plain-text threat output (when ``tool_calls`` are missing).
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import ValidationError

from state import Threat, ThreatsList
from threats_text_blocks import extract_threat_dicts_from_text


def parse_threats_list_from_text(text: str) -> Optional[ThreatsList]:
    """
    Parse JSON threat list (see ``threats_text_blocks``) into ``ThreatsList``.

    Returns ``None`` if extraction fails or validation fails.
    """
    raw = extract_threat_dicts_from_text(text)
    if not raw:
        return None

    try:
        threats: List[Threat] = [Threat(**d) for d in raw]
        return ThreatsList(threats=threats)
    except ValidationError:
        return None
