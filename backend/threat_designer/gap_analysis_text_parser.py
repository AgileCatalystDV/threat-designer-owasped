"""
Build ``ContinueThreatModeling`` from plain-text gap-analysis output.
"""

from __future__ import annotations

from typing import Optional

from pydantic import ValidationError

from gap_analysis_text_blocks import extract_continue_dict_from_text
from state import ContinueThreatModeling


def parse_continue_threat_modeling_from_text(text: str) -> Optional[ContinueThreatModeling]:
    """
    Parse XML / JSON gap output into ``ContinueThreatModeling``.

    Returns ``None`` if extraction fails or validation fails.
    """
    raw = extract_continue_dict_from_text(text)
    if not raw:
        return None
    try:
        return ContinueThreatModeling(**raw)
    except ValidationError:
        return None
