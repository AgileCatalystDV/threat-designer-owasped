"""
Normalize ``add_threats`` tool call arguments before ``ToolNode`` validation.

Qwen / LM Studio often send ``{\"threats\": [<dict>, ...]}``. LangChain's
``ToolNode`` validates against the tool schema using **dicts** (JSON); passing a
``ThreatsList`` Pydantic instance can still fail with
``Input should be a valid dictionary or instance of ThreatsList``. We coerce to
the session's ``ThreatsList`` / ``DynThreatsList`` and then ``model_dump()`` so
the bound tool receives a plain dict.
"""

from __future__ import annotations

from typing import Any, List, Type

from langchain_core.messages import AIMessage, ToolMessage
from monitoring import logger
from state import ThreatState, ThreatsList, create_constrained_threat_model

# Substring LangChain/Pydantic emit when tool args do not match the schema.
ADD_THREATS_SCHEMA_VALIDATION_ERROR_SNIPPET = (
    "Input should be a valid dictionary or instance of ThreatsList"
)


def resolve_threats_list_model(state: ThreatState):
    """``ThreatsList`` or dynamic subclass (same logic as ``workflow_threats._build_session_tools``)."""
    assets = state.get("assets")
    system_architecture = state.get("system_architecture")

    asset_names: set[str] = set()
    if assets and assets.assets:
        asset_names = {a.name for a in assets.assets}

    source_cats: set[str] = set()
    if system_architecture and system_architecture.threat_sources:
        source_cats = {s.category for s in system_architecture.threat_sources}

    if not asset_names and not source_cats:
        return ThreatsList

    try:
        _, dyn = create_constrained_threat_model(asset_names, source_cats)
        return dyn
    except Exception:
        return ThreatsList


def count_add_threats_tool_schema_errors(messages: List[Any]) -> int:
    """Count ``ToolMessage`` bodies that report the known ``add_threats`` schema error."""
    if not messages:
        return 0
    n = 0
    for m in messages:
        if not isinstance(m, ToolMessage):
            continue
        c = getattr(m, "content", "") or ""
        if "add_threats" in c and ADD_THREATS_SCHEMA_VALIDATION_ERROR_SNIPPET in c:
            n += 1
    return n


def _coerce_threats_arg_to_model_dump(threats_model: Type[ThreatsList], t: Any) -> Any:
    """Build validated ``ThreatsList``-shaped dict for ``ToolNode``."""
    if t is None:
        return t
    try:
        if isinstance(t, list) and t and isinstance(t[0], dict):
            if "name" in t[0] and "stride_category" in t[0]:
                return threats_model(threats=t).model_dump()
        if isinstance(t, dict) and "threats" in t and isinstance(t["threats"], list):
            return threats_model.model_validate(t).model_dump()
        if isinstance(t, ThreatsList):
            return threats_model.model_validate(t.model_dump()).model_dump()
    except Exception as e:
        logger.warning(
            "add_threats: could not coerce threats to model_dump",
            error=str(e),
        )
    return t


def coerce_add_threats_tool_calls_in_messages(
    messages: List[Any], state: ThreatState
) -> List[Any]:
    """
    Wrap raw threat dict lists in ``ThreatsList`` / dynamic model for ``add_threats``.
    """
    if not messages:
        return messages
    last = messages[-1]
    if not isinstance(last, AIMessage) or not getattr(last, "tool_calls", None):
        return messages

    threats_model = resolve_threats_list_model(state)
    new_calls = []
    for tc in last.tool_calls:
        tc_dict = tc if isinstance(tc, dict) else {
            "name": getattr(tc, "name", ""),
            "args": dict(getattr(tc, "args", {}) or {}),
            "id": getattr(tc, "id", None),
            "type": getattr(tc, "type", "tool_call"),
        }
        args = dict(tc_dict.get("args") or {})
        if tc_dict.get("name") == "add_threats":
            t = args.get("threats")
            args["threats"] = _coerce_threats_arg_to_model_dump(threats_model, t)
        new_calls.append({**tc_dict, "args": args})

    new_last = last.model_copy(update={"tool_calls": new_calls})
    return messages[:-1] + [new_last]
