"""Tests for [TOOL_REQUEST] / [END_TOOL_REQUEST] plain-text normalization."""

import pytest

from tool_request_markers import (
    MARKER_END,
    MARKER_START,
    extract_inner_payload,
    normalize_text_for_structured_fallback,
    slice_from_last_gemma_channel_tool_request,
)


@pytest.mark.unit
def test_no_markers_returns_original():
    raw = "Type: Asset\nName: Foo\nDescription: bar\nCriticality: High"
    assert normalize_text_for_structured_fallback(raw) == raw


@pytest.mark.unit
def test_prefix_stripped_inner_kept():
    raw = """Some thinking noise here.

[TOOL_REQUEST]
Type: Asset
Name: ApiGateway
Description: Gateway
Criticality: High
[END_TOOL_REQUEST]
trailing ignored
"""
    out = normalize_text_for_structured_fallback(raw)
    assert "Some thinking" not in out
    assert "trailing ignored" not in out
    assert "ApiGateway" in out
    assert MARKER_START not in out
    assert MARKER_END not in out


@pytest.mark.unit
def test_missing_end_returns_original():
    raw = "intro [TOOL_REQUEST] only start"
    assert normalize_text_for_structured_fallback(raw) == raw
    assert extract_inner_payload(raw) is None


@pytest.mark.unit
def test_extract_inner_payload_json():
    raw = '[TOOL_REQUEST]\n{"assets":[]}\n[END_TOOL_REQUEST]'
    assert extract_inner_payload(raw) == '{"assets":[]}'


@pytest.mark.unit
def test_slice_gemma_channel_after_sentence_dot():
    """``.<channel|>`` — slice starts at ``<`` (suffix is enough)."""
    text = "intro.<channel|>[TOOL_REQUEST]\n{}\n[END_TOOL_REQUEST]"
    out = slice_from_last_gemma_channel_tool_request(text)
    assert out.startswith("<channel|>[TOOL_REQUEST]")


@pytest.mark.unit
def test_slice_gemma_channel_without_sentence_dot():
    text = "intro x<channel|>[TOOL_REQUEST]\n{}\n[END_TOOL_REQUEST]"
    out = slice_from_last_gemma_channel_tool_request(text)
    assert out.startswith("<channel|>[TOOL_REQUEST]")


@pytest.mark.unit
def test_slice_gemma_channel_no_match_returns_original():
    raw = "Type: Asset\nName: Foo\n"
    assert slice_from_last_gemma_channel_tool_request(raw) == raw
