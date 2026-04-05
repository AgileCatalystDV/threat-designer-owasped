"""
Build ``ThreatsList`` from plain-text threat output (when ``tool_calls`` are missing).
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import ValidationError

from state import Threat, ThreatsList
from structured_tool_json import tool_arguments_if_name, try_parse_json_object
from threats_text_blocks import extract_threat_dicts_from_text


def parse_threats_list_from_text(text: str) -> Optional[ThreatsList]:
    """
    Parse JSON threat list (see ``threats_text_blocks``) into ``ThreatsList``.

    Also accepts ``{"name": "ThreatsList", "arguments": {"threats": [...]}}``.

    Returns ``None`` if extraction fails or validation fails.
    """
    j = try_parse_json_object(text)
    if j:
        args = tool_arguments_if_name(j, "ThreatsList")
        if args is not None:
            try:
                return ThreatsList.model_validate(args)
            except ValidationError:
                pass
        if "threats" in j and isinstance(j.get("threats"), list):
            try:
                return ThreatsList.model_validate(j)
            except ValidationError:
                pass
    raw = extract_threat_dicts_from_text(text)
    if not raw:
        return None

    try:
        threats: List[Threat] = [Threat(**d) for d in raw]
        return ThreatsList(threats=threats)
    except ValidationError:
        return None
