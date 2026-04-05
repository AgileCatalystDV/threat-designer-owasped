"""
Build ``FlowsList`` from plain-text flow prompt output (when tool_calls are missing).
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import ValidationError

from flows_text_blocks import extract_flows_dict_from_text
from state import DataFlow, FlowsList, ThreatSource, TrustBoundary
from structured_tool_json import tool_arguments_if_name, try_parse_json_object


def parse_flows_list_from_text(text: str) -> Optional[FlowsList]:
    """
    Parse ``<data_flow>``, ``<trust_boundary>``, and threat table into ``FlowsList``.

    Also accepts JSON: ``{"name": "FlowsList", "arguments": {...}}`` with keys
    ``data_flows``, ``trust_boundaries``, ``threat_sources``.

    Returns ``None`` if extraction fails or validation fails for all rows.
    """
    j = try_parse_json_object(text)
    if j:
        args = tool_arguments_if_name(j, "FlowsList")
        if args is not None:
            try:
                return FlowsList.model_validate(args)
            except ValidationError:
                pass
        if all(k in j for k in ("data_flows", "trust_boundaries", "threat_sources")):
            try:
                return FlowsList.model_validate(j)
            except ValidationError:
                pass
    raw = extract_flows_dict_from_text(text)
    if not raw:
        return None

    try:
        data_flows: List[DataFlow] = [DataFlow(**d) for d in raw["data_flows"]]
        trust_boundaries: List[TrustBoundary] = [
            TrustBoundary(**d) for d in raw["trust_boundaries"]
        ]
        threat_sources: List[ThreatSource] = [
            ThreatSource(**d) for d in raw["threat_sources"]
        ]
        return FlowsList(
            data_flows=data_flows,
            trust_boundaries=trust_boundaries,
            threat_sources=threat_sources,
        )
    except ValidationError:
        return None
