"""
Unit tests for plain-text threat JSON extraction (Qwen ``<parameter=threats>``).

Uses ``threats_text_blocks`` (stdlib + json) and ``threats_text_parser`` for ``ThreatsList``.
"""

from pathlib import Path

import pytest

from threats_text_blocks import extract_threat_dicts_from_text, merge_threat_rows_by_name

SAMPLE_TOOL_WRAPPER = """
</redacted_thinking>

<tool_call>
<function=add_threats>
<parameter=threats>
[{"name": "SQL Injection via Web Application API Endpoints", "stride_category": "Tampering", "description": "External Threat Actors, with knowledge of application structure and access to public-facing endpoints, can inject malicious SQL queries through unvalidated input parameters, which leads to unauthorized database data access or modification, negatively impacting Database.", "target": "Web Application API Endpoints", "impact": "Unauthorized access to sensitive user information and business-critical records; potential data exfiltration or corruption of critical business data", "likelihood": "High", "mitigations": ["Implement parameterized queries for all database calls in the Web Application API Endpoints", "Deploy input validation and sanitization at the API layer before any database interaction", "Use ORM frameworks with built-in SQL injection protection"], "source": "External Threat Actors", "prerequisites": ["Public-facing API endpoints accessible without authentication or with weak authentication", "User-supplied input not properly validated or sanitized before database queries"], "vector": "HTTP request parameters, query strings, form inputs"}]
</parameter>
</function>
</tool_call>
"""


@pytest.mark.unit
def test_extract_from_parameter_threats_block():
    rows = extract_threat_dicts_from_text(SAMPLE_TOOL_WRAPPER)
    assert rows is not None
    assert len(rows) == 1
    assert rows[0]["name"] == "SQL Injection via Web Application API Endpoints"
    assert rows[0]["stride_category"] == "Tampering"
    assert rows[0]["likelihood"] == "High"
    assert len(rows[0]["mitigations"]) >= 2


@pytest.mark.unit
def test_extract_from_wrapped_object():
    text = (
        '{"threats": [{"name": "Test Threat", "stride_category": "Spoofing", '
        '"description": "External Threat Actors with access can spoof sessions which leads to account takeover, negatively impacting Target.", '
        '"target": "Target", "impact": "Loss of account integrity and confidentiality for users.", '
        '"likelihood": "Low", "mitigations": ["Use MFA", "Rotate sessions"], '
        '"source": "External Threat Actors", "prerequisites": ["Network access"], "vector": "HTTP"}]}'
    )
    rows = extract_threat_dicts_from_text(text)
    assert rows is not None
    assert len(rows) == 1
    assert rows[0]["name"] == "Test Threat"


@pytest.mark.unit
def test_extract_returns_none_for_empty():
    assert extract_threat_dicts_from_text("") is None
    assert extract_threat_dicts_from_text("no json here") is None


@pytest.mark.unit
def test_extract_strips_thinking_then_finds_json():
    text = (
        "<redacted_thinking>\nreasoning\n</redacted_thinking>\n"
        '<parameter=threats>[{"name": "T", "stride_category": "Tampering", '
        '"description": "Malicious Internal Actors with access can tamper data which leads to integrity loss, negatively impacting Database.", '
        '"target": "Database", "impact": "Corruption of business records and regulatory exposure.", '
        '"likelihood": "Medium", "mitigations": ["Integrity checks", "Audit logs"], '
        '"source": "Malicious Internal Actors", "prerequisites": ["DB access"], '
        '"vector": "SQL"}]\n'
    )
    rows = extract_threat_dicts_from_text(text)
    assert rows is not None
    assert len(rows) == 1


@pytest.mark.unit
def test_parse_threats_list_from_text_roundtrip():
    from threats_text_parser import parse_threats_list_from_text

    tl = parse_threats_list_from_text(SAMPLE_TOOL_WRAPPER)
    assert tl is not None
    assert len(tl.threats) == 1
    assert tl.threats[0].stride_category == "Tampering"


MINIMAL_THREAT = (
    '"name": "T1", "stride_category": "Tampering", '
    '"description": "External Threat Actors with access can tamper which leads to loss, negatively impacting Database.", '
    '"target": "Database", "impact": "Data loss.", '
    '"likelihood": "Medium", "mitigations": ["A", "B"], '
    '"source": "External Threat Actors", "prerequisites": ["x"], "vector": "net"'
)


@pytest.mark.unit
def test_truncated_array_keeps_complete_objects_only():
    """Incomplete tail after the last full object is ignored."""
    text = (
        "<parameter=threats>[{"
        + MINIMAL_THREAT
        + "}, {"
        + MINIMAL_THREAT.replace("T1", "T2")
        + "}, {\"name\": \"Cut off"
    )
    rows = extract_threat_dicts_from_text(text)
    assert rows is not None
    assert len(rows) == 2
    assert rows[0]["name"] == "T1"
    assert rows[1]["name"] == "T2"


@pytest.mark.unit
def test_multiple_parameter_blocks_merged_dedupe_by_name():
    """Same transcript repeated (e.g. retries): one row per threat name."""
    block = (
        "<parameter=threats>[{"
        + MINIMAL_THREAT
        + "}, {"
        + MINIMAL_THREAT.replace("T1", "T2")
        + "}]</parameter>\n"
    )
    text = block + block
    rows = extract_threat_dicts_from_text(text)
    assert rows is not None
    assert len(rows) == 2
    names = {r["name"] for r in rows}
    assert names == {"T1", "T2"}


@pytest.mark.unit
def test_merge_threat_rows_by_name_last_wins():
    a = {"name": "Same", "stride_category": "Tampering", "likelihood": "Low"}
    b = {**a, "likelihood": "High"}
    merged = merge_threat_rows_by_name([a, b])
    assert len(merged) == 1
    assert merged[0]["likelihood"] == "High"


@pytest.mark.unit
def test_tmmodelthreatsthinkinghangsqwen_doc_when_present():
    """
    Long transcript with repeated ``add_threats`` / tool errors (see QA doc).

    Requires ``docs/qa/tmmodelthreatsthinkinghangsqwen.md`` saved on disk.
    """
    doc = (
        Path(__file__).resolve().parent.parent.parent
        / "docs"
        / "qa"
        / "tmmodelthreatsthinkinghangsqwen.md"
    )
    if not doc.is_file() or doc.stat().st_size < 1000:
        pytest.skip("docs/qa/tmmodelthreatsthinkinghangsqwen.md missing or empty on disk")
    text = doc.read_text(encoding="utf-8")
    rows = extract_threat_dicts_from_text(text)
    assert rows is not None
    assert len(rows) == 12
    from threats_text_parser import parse_threats_list_from_text

    tl = parse_threats_list_from_text(text)
    assert tl is not None
    assert len(tl.threats) == 12


@pytest.mark.unit
def test_tmfinalthreatmodelingrequestresponseqwen_full_file():
    """
    Regression: Qwen export with full request + assistant ``add_threats`` (12 threats).

    See ``docs/qa/tmfinalthreatmodelingrequestresponseqwen.md``.
    """
    doc = (
        Path(__file__).resolve().parent.parent.parent
        / "docs"
        / "qa"
        / "tmfinalthreatmodelingrequestresponseqwen.md"
    )
    if not doc.is_file() or doc.stat().st_size < 1000:
        pytest.skip("docs/qa/tmfinalthreatmodelingrequestresponseqwen.md missing or empty on disk")
    text = doc.read_text(encoding="utf-8")
    rows = extract_threat_dicts_from_text(text)
    assert rows is not None
    assert len(rows) == 12
    from threats_text_parser import parse_threats_list_from_text

    tl = parse_threats_list_from_text(text)
    assert tl is not None
    assert len(tl.threats) == 12
    assert tl.threats[0].name.startswith("SQL Injection")


@pytest.mark.unit
def test_threatsmodelingresponseqwen_doc_when_present():
    """Regression: full Qwen export in ``docs/qa/threatsmodelingresponseqwen.md`` (12 threats)."""
    doc = (
        Path(__file__).resolve().parent.parent.parent
        / "docs"
        / "qa"
        / "threatsmodelingresponseqwen.md"
    )
    if not doc.is_file() or doc.stat().st_size < 100:
        pytest.skip("docs/qa/threatsmodelingresponseqwen.md missing or empty on disk")
    text = doc.read_text(encoding="utf-8")
    rows = extract_threat_dicts_from_text(text)
    assert rows is not None
    assert len(rows) == 12
    from threats_text_parser import parse_threats_list_from_text

    tl = parse_threats_list_from_text(text)
    assert tl is not None
    assert len(tl.threats) == 12
