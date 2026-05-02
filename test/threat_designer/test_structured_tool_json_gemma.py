"""
Gemma / tool-style JSON payloads: real doc + projected FlowsList / ThreatsList JSON.

Canonical captures under ``test/threat_designer/fixtures/`` (PR-A zelfstandig).
Spiegels / commentary: ``docs/qa/assetresponsegemma4.md``,
``docs/qa/dataflowresponsegemma4.md``, ``docs/llm-assets-format-and-improvements.md``.
"""

from pathlib import Path

import pytest

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
GEMMA4_ASSET_CAPTURE = _FIXTURES / "gemma4_asset_capture.md"
GEMMA4_DATAFLOW_CAPTURE = _FIXTURES / "gemma4_dataflow_capture.md"

from asset_text_parser import parse_assets_list_from_text
from flows_text_parser import parse_flows_list_from_text
from structured_tool_json import repair_json_llm_typos, try_parse_json_object
from threats_text_parser import parse_threats_list_from_text
from tool_request_markers import (
    normalize_text_for_structured_fallback,
    slice_from_last_gemma_channel_tool_request,
)


@pytest.mark.unit
def test_repair_json_llm_typos_gemma_malformed_key():
    bad = '{"type": "Asset", "、name": "Web App Config", "description": "x", "criticality": "Medium"}'
    fixed = repair_json_llm_typos(bad)
    d = try_parse_json_object(fixed)
    assert d is not None
    assert d.get("name") == "Web App Config"


@pytest.mark.unit
def test_gemma4_assetresponse_full_tool_marker_and_json():
    """Echte output uit Gemma-capture (google/gemma-4-26b-a4b)."""
    doc = GEMMA4_ASSET_CAPTURE
    text = doc.read_text(encoding="utf-8")
    start = text.find("I will use the tool")
    assert start != -1
    chunk = text[start:]
    inner = normalize_text_for_structured_fallback(chunk)
    al = parse_assets_list_from_text(inner)
    assert al is not None
    assert len(al.assets) == 8
    names = [a.name for a in al.assets]
    assert "Database" in names
    assert "Web App Config" in names
    assert al.assets[0].type == "Asset"
    assert al.assets[-1].criticality == "Low"


@pytest.mark.unit
def test_gemma4_dataflowresponse_full_tool_marker_and_json():
    """Echte output uit Gemma FlowsList-capture (google/gemma-4-26b-a4b).

    Filtering: ``slice_from_last_gemma_channel_tool_request`` (punt-variant of zonder punt)
    → ``normalize_text_for_structured_fallback`` → JSON tussen markers.
    """
    doc = GEMMA4_DATAFLOW_CAPTURE
    text = doc.read_text(encoding="utf-8")
    chunk = slice_from_last_gemma_channel_tool_request(text)
    assert "<channel|>[TOOL_REQUEST]" in chunk
    inner = normalize_text_for_structured_fallback(chunk)
    fl = parse_flows_list_from_text(inner)
    assert fl is not None
    assert len(fl.data_flows) == 10
    assert len(fl.threat_sources) == 5
    assert len(fl.trust_boundaries) == 4
    assert fl.data_flows[0].source_entity == "Web Application"
    assert fl.data_flows[0].target_entity == "Database"
    assert "SQL" in fl.data_flows[0].flow_description
    assert fl.trust_boundaries[0].source_entity == "External API"
    assert fl.trust_boundaries[0].target_entity == "Web Application"
    assert fl.threat_sources[2].category == "External Threat Actors"


@pytest.mark.unit
def test_gemma4_dataflowresponse_other_preamble_before_dot_channel():
    """Zelfde FlowsList-JSON als fixture, maar andere zin vóór ``.<channel|>[TOOL_REQUEST]``."""
    doc = GEMMA4_DATAFLOW_CAPTURE
    text = doc.read_text(encoding="utf-8")
    chunk = slice_from_last_gemma_channel_tool_request(text)
    inner = normalize_text_for_structured_fallback(chunk)
    baseline_flows = parse_flows_list_from_text(inner)
    assert baseline_flows is not None

    replaced = text.replace(
        "Format as requested.<channel|>[TOOL_REQUEST]",
        "Here is the structured output.<channel|>[TOOL_REQUEST]",
        1,
    )
    chunk2 = slice_from_last_gemma_channel_tool_request(replaced)
    inner2 = normalize_text_for_structured_fallback(chunk2)
    fl2 = parse_flows_list_from_text(inner2)
    assert fl2 is not None
    assert len(fl2.data_flows) == len(baseline_flows.data_flows)


@pytest.mark.unit
def test_gemma4_dataflowresponse_without_dot_before_channel():
    """Geen punt vóór ``<channel|>[TOOL_REQUEST]`` — tweede strategie (plain suffix)."""
    json_line = (
        '{"name": "FlowsList", "arguments": {"data_flows": [{"flow_description": "x", '
        '"source_entity": "A", "target_entity": "B"}], '
        '"trust_boundaries": [{"purpose": "p", "source_entity": "A", "target_entity": "B"}], '
        '"threat_sources": [{"category": "c", "description": "d", "example": "e"}]}}'
    )
    text = f"""noise
x<channel|>[TOOL_REQUEST]
{json_line}
[END_TOOL_REQUEST]
"""
    chunk = slice_from_last_gemma_channel_tool_request(text)
    assert chunk.startswith("<channel|>[TOOL_REQUEST]")
    inner = normalize_text_for_structured_fallback(chunk)
    fl = parse_flows_list_from_text(inner)
    assert fl is not None
    assert len(fl.data_flows) == 1
    assert fl.data_flows[0].source_entity == "A"


@pytest.mark.unit
def test_flows_list_tool_json_projection():
    """Zelfde patroon als Gemma AssetsList, gesynthetiseerd voor FlowsList."""
    payload = """
[TOOL_REQUEST]
{"name": "FlowsList", "arguments": {"data_flows": [{"flow_description": "Browser to Web", "source_entity": "Browser", "target_entity": "Web Application"}], "trust_boundaries": [{"purpose": "User to app", "source_entity": "Browser", "target_entity": "Web Application"}], "threat_sources": [{"category": "External Threat Actors", "description": "Attacker", "example": "Script kiddie"}]}}
[END_TOOL_REQUEST]
"""
    inner = normalize_text_for_structured_fallback(payload)
    fl = parse_flows_list_from_text(inner)
    assert fl is not None
    assert len(fl.data_flows) == 1
    assert fl.data_flows[0].target_entity == "Web Application"
    assert len(fl.threat_sources) == 1


@pytest.mark.unit
def test_threats_list_tool_json_projection():
    """Zelfde patroon als Gemma, gesynthetiseerd voor ThreatsList."""
    payload = """
[TOOL_REQUEST]
{"name": "ThreatsList", "arguments": {"threats": [{"name": "Test Spoof", "stride_category": "Spoofing", "description": "External Threat Actors with access can spoof sessions which leads to account takeover, negatively impacting Target.", "target": "Target", "impact": "Account loss.", "likelihood": "Low", "mitigations": ["MFA", "Session binding"], "source": "External Threat Actors", "prerequisites": ["Net"], "vector": "HTTP"}]}}
[END_TOOL_REQUEST]
"""
    inner = normalize_text_for_structured_fallback(payload)
    tl = parse_threats_list_from_text(inner)
    assert tl is not None
    assert len(tl.threats) == 1
    assert tl.threats[0].name == "Test Spoof"
    assert tl.threats[0].stride_category == "Spoofing"

@pytest.mark.unit
def test_try_parse_json_object_balanced_with_trailing_garbage():
    """Na eerste ``}`` mag tekst volgen; backwards compatible met strikt JSON."""
    from structured_tool_json import try_parse_json_object

    blob = (
        '{"name": "AssetsList", "arguments": {"assets": []}}'
        " and ignore this"
    )
    d = try_parse_json_object(blob)
    assert d is not None
    assert d.get("name") == "AssetsList"

