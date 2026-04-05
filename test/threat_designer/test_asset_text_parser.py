"""
Unit tests for plain-text asset block extraction (prompt output_format).

Uses `asset_text_blocks` only (stdlib + regex) — no langgraph/langchain required.
`asset_text_parser.parse_assets_list_from_text` builds Pydantic models; run in Docker / full venv.
"""

import pytest

from asset_text_blocks import extract_asset_dicts_from_text

SAMPLE_TWO_BLOCKS = """
## Assets

Type: Asset

Name: Database

Description: Central data store containing application data and user information.

Criticality: High


Type: Entity

Name: External API Integration

Description: Third-party service integration point at an external trust boundary.

Criticality: High
"""


@pytest.mark.unit
def test_extract_two_blocks():
    rows = extract_asset_dicts_from_text(SAMPLE_TWO_BLOCKS)
    assert rows is not None
    assert len(rows) == 2
    assert rows[0]["type"] == "Asset"
    assert rows[0]["name"] == "Database"
    assert rows[0]["criticality"] == "High"
    assert "Central data store" in rows[0]["description"]
    assert rows[1]["type"] == "Entity"
    assert rows[1]["name"] == "External API Integration"


@pytest.mark.unit
def test_extract_returns_none_for_empty_string():
    assert extract_asset_dicts_from_text("") is None
    assert extract_asset_dicts_from_text("   ") is None


@pytest.mark.unit
def test_extract_strips_thinking_then_finds_blocks():
    text = (
        "<redacted_thinking>\n"
        "some reasoning\n"
        "</redacted_thinking>\n\n"
        "Type: Asset\n\n"
        "Name: Queue\n\n"
        "Description: Message queue for async work.\n\n"
        "Criticality: Medium\n"
    )
    rows = extract_asset_dicts_from_text(text)
    assert rows is not None
    assert len(rows) == 1
    assert rows[0]["name"] == "Queue"
    assert rows[0]["criticality"] == "Medium"


@pytest.mark.unit
def test_extract_assetresponseqwen_answer_section_count():
    """Volledige answer-sectie uit docs/qa/assetresponseqwen.md: 5 assets + 4 entities."""
    from pathlib import Path

    doc = Path(__file__).resolve().parent.parent.parent / "docs" / "qa" / "assetresponseqwen.md"
    text = doc.read_text(encoding="utf-8")
    start = text.find("## Assets")
    assert start != -1
    chunk = text[start:]
    rows = extract_asset_dicts_from_text(chunk)
    assert rows is not None
    assert len(rows) == 9
    types = [r["type"] for r in rows]
    assert types.count("Asset") == 5
    assert types.count("Entity") == 4

@pytest.mark.unit
def test_parse_assets_list_from_text_plain_blocks_backwards_compatible():
    """Type:/Name: pad blijft primair als er geen geldig JSON-object is."""
    from asset_text_parser import parse_assets_list_from_text

    al = parse_assets_list_from_text(SAMPLE_TWO_BLOCKS)
    assert al is not None
    assert len(al.assets) == 2
    assert al.assets[0].name == "Database"
    assert al.assets[1].type == "Entity"


@pytest.mark.unit
def test_parse_assets_list_json_with_leading_prose():
    """Eerste gebalanceerde JSON na ruis (zelfde payload als tool-wrapper)."""
    from asset_text_parser import parse_assets_list_from_text

    core = (
        '{"name": "AssetsList", "arguments": {"assets": ['
        '{"type": "Asset", "name": "X", "description": "d", "criticality": "High"}'
        "]}}"
    )
    wrapped = "Here is the output.\n\n" + core + "\n\nThanks."
    al = parse_assets_list_from_text(wrapped)
    assert al is not None
    assert len(al.assets) == 1
    assert al.assets[0].name == "X"


@pytest.mark.unit
def test_parse_assets_list_plain_text_unaffected_by_brace_in_description():
    """Beschrijving met accolades: nog steeds Type:-extractie als geen JSON root."""
    from asset_text_parser import parse_assets_list_from_text

    text = """
Type: Asset
Name: Config
Description: JSON-like {not: valid} but not a root object at start.
Criticality: Low
"""
    al = parse_assets_list_from_text(text)
    assert al is not None
    assert al.assets[0].name == "Config"

