"""
Parse plain-text asset inventories from the prompt output_format (Type/Name/Description/Criticality).

Used when the LLM returns prose instead of OpenAI-style tool_calls (common with local models).
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import ValidationError

from asset_text_blocks import extract_asset_dicts_from_text
from state import Assets, AssetsList


def parse_assets_list_from_text(text: str) -> Optional[AssetsList]:
    """
    Parse prompt-style asset blocks into AssetsList.

    Returns None if no valid blocks are found or all rows fail validation.
    """
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
