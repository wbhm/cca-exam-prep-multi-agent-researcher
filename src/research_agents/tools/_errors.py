"""Single constructor for structured tool errors.

Every handler builds its failure payload here so the emitted JSON and the
``ToolErrorResponse`` model cannot drift apart: the model *is* the
serializer.
"""

from __future__ import annotations

from research_agents.models.errors import ToolErrorResponse


def error_response(
    error_type: str,
    source: str,
    message: str,
    *,
    retry_eligible: bool = False,
    fallback_available: bool = False,
    partial_data: dict | None = None,
) -> str:
    """Return a JSON string for a structured tool error."""
    return ToolErrorResponse(
        error_type=error_type,
        source=source,
        message=message,
        retry_eligible=retry_eligible,
        fallback_available=fallback_available,
        partial_data=partial_data,
    ).model_dump_json()
