"""Structured error models for tool responses.

CCA Key Concept: Subagents must return structured error information when
something goes wrong — not just "success" or "failure." The coordinator
needs error_type, retry_eligible, and partial_data to make informed
decisions (retry, fallback, flag gap). In this project the coordinator
implements the "flag gap" branch programmatically
(``coordinator.collect_gaps``); retry and fallback are left to the caller.

Handlers never build this payload by hand: ``tools._errors.error_response``
serializes the model, so the JSON on the wire and this schema cannot drift.

Anti-pattern: SilentFailureResponse returns {"status":"success","data":null}
which is indistinguishable from "no relevant data found."
"""

from __future__ import annotations

from pydantic import BaseModel


class ToolErrorResponse(BaseModel):
    """Structured error context returned by tool handlers on failure.

    Gives the coordinator a decision tree:
    - retry_eligible=True → retry (timeouts, rate limits)
    - fallback_available=True → try alternative source
    - Both False → flag gap in report
    """

    status: str = "error"
    error_type: str  # "timeout", "not_found", "rate_limit", "invalid_input", "parse_error"
    source: str  # which service/URL failed
    message: str
    retry_eligible: bool
    fallback_available: bool
    partial_data: dict | None = None


class SilentFailureResponse(BaseModel):
    """Anti-pattern: returns success with null data on error.

    The coordinator cannot distinguish between:
    - "no relevant data exists" (legitimate empty result)
    - "the subagent failed to retrieve data" (error that needs handling)

    This is the silent failure anti-pattern the CCA exam tests explicitly.
    """

    status: str = "success"
    data: None = None
