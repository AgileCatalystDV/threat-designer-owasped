"""
Coercion of ``add_threats`` tool args: list of dicts → ``ThreatsList`` (Qwen/LM Studio).
"""

import pytest


@pytest.mark.unit
def test_coerce_add_threats_wraps_list_as_threatslist():
    from langchain_core.messages import AIMessage

    from state import (
        Assets,
        AssetsList,
        DataFlow,
        FlowsList,
        ThreatSource,
        TrustBoundary,
    )
    from add_threats_tool_args import (
        coerce_add_threats_tool_calls_in_messages,
        resolve_threats_list_model,
    )

    assets = AssetsList(
        assets=[
            Assets(
                type="Asset",
                name="Database",
                description="d",
                criticality="High",
            ),
        ]
    )
    flows = FlowsList(
        data_flows=[
            DataFlow(
                flow_description="a",
                source_entity="Database",
                target_entity="Database",
            )
        ],
        trust_boundaries=[
            TrustBoundary(
                purpose="p",
                source_entity="a",
                target_entity="b",
            )
        ],
        threat_sources=[
            ThreatSource(
                category="External Threat Actors",
                description="d",
                example="e",
            )
        ],
    )
    state = {"assets": assets, "system_architecture": flows}
    row = {
        "name": "Test threat",
        "stride_category": "Tampering",
        "description": (
            "External Threat Actors with x can y which leads to z, "
            "negatively impacting Database."
        ),
        "target": "Database",
        "impact": "i",
        "likelihood": "Low",
        "mitigations": ["m1", "m2"],
        "source": "External Threat Actors",
        "prerequisites": ["p"],
        "vector": "v",
    }
    msg = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "add_threats",
                "args": {"threats": [row]},
                "id": "call-1",
                "type": "tool_call",
            }
        ],
    )
    out = coerce_add_threats_tool_calls_in_messages([msg], state)
    args = out[-1].tool_calls[0]["args"]
    assert isinstance(args["threats"], dict)
    threats_model = resolve_threats_list_model(state)
    tl = threats_model.model_validate(args["threats"])
    assert len(tl.threats) == 1
    assert tl.threats[0].name == "Test threat"


@pytest.mark.unit
def test_count_add_threats_schema_errors():
    from langchain_core.messages import ToolMessage

    from add_threats_tool_args import (
        ADD_THREATS_SCHEMA_VALIDATION_ERROR_SNIPPET,
        count_add_threats_tool_schema_errors,
    )

    bad = ToolMessage(
        content=(
            "Error invoking tool 'add_threats': "
            + ADD_THREATS_SCHEMA_VALIDATION_ERROR_SNIPPET
        ),
        tool_call_id="x",
    )
    assert count_add_threats_tool_schema_errors([bad]) == 1
    assert count_add_threats_tool_schema_errors([]) == 0
