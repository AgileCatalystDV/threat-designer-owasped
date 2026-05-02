"""
Build ``FlowsList`` from plain-text flow prompt output (when tool_calls are missing).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from flows_text_blocks import extract_flows_dict_from_text
from state import DataFlow, FlowsList, ThreatSource, TrustBoundary
from structured_tool_json import tool_arguments_if_name, try_parse_json_object


def _coerce_example_field(value: Any) -> str:
    """Map ``examples`` / lists to ``ThreatSource.example`` (single string)."""
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(x) for x in value)
    return str(value)


def _normalize_threat_source_dict(item: Any) -> Optional[Dict[str, str]]:
    """
    Coerce one threat actor object to ``ThreatSource`` keys.

    Accepts ``example`` or ``examples`` (string or list), and common TitleCase keys.
    """
    if not isinstance(item, dict):
        return None
    lower = {str(k).lower(): v for k, v in item.items()}
    cat = lower.get("category")
    if cat is None or (isinstance(cat, str) and not cat.strip()):
        return None
    desc = lower.get("description")
    desc = "" if desc is None else str(desc)
    ex = lower.get("example")
    if ex is None:
        ex = lower.get("examples")
    ex = _coerce_example_field(ex)
    return {
        "category": str(cat).strip(),
        "description": desc,
        "example": ex,
    }


def _normalize_flows_list_arguments(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Align LLM JSON variants with ``FlowsList`` / ``ThreatSource``.

    - ``threat_actors`` → ``threat_sources`` (when ``threat_sources`` is absent).
    - Per item: ``examples`` → ``example``; list values joined.
    """
    out: Dict[str, Any] = dict(args)
    if "threat_sources" not in out or out.get("threat_sources") is None:
        alt = out.pop("threat_actors", None)
        if alt is not None:
            out["threat_sources"] = alt
    else:
        out.pop("threat_actors", None)
    ts = out.get("threat_sources")
    if isinstance(ts, list):
        normalized: List[Dict[str, str]] = []
        for item in ts:
            row = _normalize_threat_source_dict(item)
            if row is not None:
                normalized.append(row)
        out["threat_sources"] = normalized
    return out


def _json_has_flows_list_shape(j: Dict[str, Any]) -> bool:
    has_actors = "threat_sources" in j or "threat_actors" in j
    return (
        "data_flows" in j
        and "trust_boundaries" in j
        and has_actors
    )


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
                return FlowsList.model_validate(_normalize_flows_list_arguments(args))
            except ValidationError:
                pass
        if _json_has_flows_list_shape(j):
            try:
                return FlowsList.model_validate(_normalize_flows_list_arguments(j))
            except ValidationError:
                pass
    raw = extract_flows_dict_from_text(text)
    if not raw:
        return None

    try:
        raw = _normalize_flows_list_arguments(raw)
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
