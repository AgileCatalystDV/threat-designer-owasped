"""
Unit tests for plain-text flow block extraction (data_flow, trust_boundary, threat table).

Uses `flows_text_blocks` (stdlib + regex) and `flows_text_parser` for Pydantic `FlowsList`.
"""

import pytest

from flows_text_blocks import extract_flows_dict_from_text

SAMPLE_MINIMAL = """
<data_flow>

flow_description: Web Application queries Database for records

source_entity: Web Application

target_entity: Database

assets: [Database]

</data_flow>

<data_flow>

flow_description: Worker reads from queue

source_entity: Message Queue

target_entity: Background Worker

assets: [Queue]

</data_flow>

<trust_boundary>

purpose: Network boundary between users and app

source_entity: Browser

target_entity: Web Application

boundary_type: Network

security_controls: TLS

</trust_boundary>

## Threat Actors

| Category | Description | Examples |

|----------|-------------|----------|

| Legitimate Users | Unintentional misconfiguration | Misconfigured user |

| External Threat Actors | Attackers on public endpoints | Web attacker |

"""


@pytest.mark.unit
def test_extract_data_flows_trust_and_threats():
    d = extract_flows_dict_from_text(SAMPLE_MINIMAL)
    assert d is not None
    assert len(d["data_flows"]) == 2
    assert d["data_flows"][0]["source_entity"] == "Web Application"
    assert d["data_flows"][0]["target_entity"] == "Database"
    assert "queries Database" in d["data_flows"][0]["flow_description"]
    assert len(d["trust_boundaries"]) == 1
    assert d["trust_boundaries"][0]["purpose"].startswith("Network boundary")
    assert len(d["threat_sources"]) == 2
    assert d["threat_sources"][0]["category"] == "Legitimate Users"
    assert "Misconfigured user" in d["threat_sources"][0]["example"]


@pytest.mark.unit
def test_extract_returns_none_for_empty():
    assert extract_flows_dict_from_text("") is None
    assert extract_flows_dict_from_text("   ") is None
    assert extract_flows_dict_from_text("no tags here") is None


@pytest.mark.unit
def test_extract_strips_thinking_then_finds_blocks():
    text = (
        "<redacted_thinking>\n"
        "reasoning…\n"
        "</redacted_thinking>\n\n"
        "<data_flow>\n"
        "flow_description: X to Y\n"
        "source_entity: X\n"
        "target_entity: Y\n"
        "</data_flow>\n"
    )
    d = extract_flows_dict_from_text(text)
    assert d is not None
    assert len(d["data_flows"]) == 1
    assert d["data_flows"][0]["source_entity"] == "X"


@pytest.mark.unit
def test_parse_flows_list_from_text_roundtrip():
    from flows_text_parser import parse_flows_list_from_text

    fl = parse_flows_list_from_text(SAMPLE_MINIMAL)
    assert fl is not None
    assert len(fl.data_flows) == 2
    assert len(fl.trust_boundaries) == 1
    assert len(fl.threat_sources) == 2
    assert fl.threat_sources[1].example == "Web attacker"
