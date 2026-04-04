"""
Unit tests for plain-text gap analysis extraction (``ContinueThreatModeling``).

Uses ``gap_analysis_text_blocks`` + ``gap_analysis_text_parser`` (Pydantic).
"""

import pytest

from gap_analysis_text_blocks import extract_continue_dict_from_text

SAMPLE_XML_STOP = """
<gap_analysis_report>
<decision>STOP</decision>
<rationale>Compliance and coverage are adequate for this architecture.</rationale>
</gap_analysis_report>
"""

SAMPLE_XML_CONTINUE = """
<gap_analysis_report>
<decision>CONTINUE</decision>
<priority_actions>
<action severity="CRITICAL">Database — Add a threat for backup exfiltration.</action>
<action severity="MAJOR">API — Calibrate likelihood for public endpoints.</action>
</priority_actions>
</gap_analysis_report>
"""

SAMPLE_JSON_STOP = '{"stop": true, "gap": "", "rating": 9}'


@pytest.mark.unit
def test_xml_stop():
    d = extract_continue_dict_from_text(SAMPLE_XML_STOP)
    assert d is not None
    assert d["stop"] is True
    assert d["gap"] == ""
    assert d["rating"] == 8


@pytest.mark.unit
def test_xml_continue_actions():
    d = extract_continue_dict_from_text(SAMPLE_XML_CONTINUE)
    assert d is not None
    assert d["stop"] is False
    assert "Database" in d["gap"]
    assert "API" in d["gap"]
    assert d["rating"] == 5


@pytest.mark.unit
def test_xml_rating_tag():
    text = "<decision>STOP</decision><rating>7</rating>"
    d = extract_continue_dict_from_text(text)
    assert d is not None
    assert d["stop"] is True
    assert d["rating"] == 7


@pytest.mark.unit
def test_json_stop():
    d = extract_continue_dict_from_text(SAMPLE_JSON_STOP)
    assert d is not None
    assert d["stop"] is True
    assert d["rating"] == 9


@pytest.mark.unit
def test_parse_continue_roundtrip():
    from gap_analysis_text_parser import parse_continue_threat_modeling_from_text

    m = parse_continue_threat_modeling_from_text(SAMPLE_XML_STOP)
    assert m is not None
    assert m.stop is True
    assert m.rating == 8


@pytest.mark.unit
def test_empty_returns_none():
    assert extract_continue_dict_from_text("") is None
    assert extract_continue_dict_from_text("no decision here") is None
