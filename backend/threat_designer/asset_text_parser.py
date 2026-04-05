"""
Parse plain-text asset inventories from the prompt output_format (Type/Name/Description/Criticality).

Used when the LLM returns prose instead of OpenAI-style tool_calls (common with local models).
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import ValidationError

from asset_text_blocks import extract_asset_dicts_from_text
from state import Assets, AssetsList
from structured_tool_json import tool_arguments_if_name, try_parse_json_object


def parse_assets_list_from_text(text: str) -> Optional[AssetsList]:
    """
    Parse prompt-style asset blocks into AssetsList.

    Also accepts JSON tool payloads: ``{"name": "AssetsList", "arguments": {"assets": [...]}}``
    or ``{"assets": [...]}`` (e.g. inside ``[TOOL_REQUEST]`` … ``[END_TOOL_REQUEST]``).

    Returns None if no valid blocks are found or all rows fail validation.
    """
    j = try_parse_json_object(text)
    if j:
        args = tool_arguments_if_name(j, "AssetsList")
        if args is not None:
            try:
                return AssetsList.model_validate(args)
            except ValidationError:
                pass
        if "assets" in j and isinstance(j.get("assets"), list):
            try:
                return AssetsList.model_validate(j)
            except ValidationError:
                pass
    raw_rows = extract_asset_dicts_from_text(text)
    if not raw_rows:
        return None

    assets: List[Assets] = []
    for row in raw_rows:
        try:
            assets.append(Assets(**row))
        except ValidationError:
            continue

    if not assets:
        return None
    return AssetsList(assets=assets)
