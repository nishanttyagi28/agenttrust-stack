"""Evidence Schema v1 JSON codec."""

from __future__ import annotations

import json
from typing import Any

from agenttrust.evidence.models import Chain


def canonical_json(model: Chain) -> str:
    """Return canonical UTF-8 JSON for *model* (no trailing newline)."""
    return json.dumps(
        model.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def parse_chain(text: str) -> Chain:
    """Parse canonical or pretty JSON text into a validated Chain."""
    return Chain.model_validate_json(text)


def json_schema() -> dict[str, Any]:
    """Return the JSON Schema for Chain."""
    return Chain.model_json_schema()
