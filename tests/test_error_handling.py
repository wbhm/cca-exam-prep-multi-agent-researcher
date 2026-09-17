"""Tests for structured error handling vs silent failures.

Compares the correct pattern (ToolErrorResponse with retry_eligible,
error_type, etc.) against the silent failure anti-pattern.
"""

from __future__ import annotations

import json

import pytest

from research_agents.anti_patterns.silent_failures import handle_fetch_page_silent
from research_agents.models.errors import ToolErrorResponse
from research_agents.services.container import ServiceContainer
from research_agents.tools.handlers import dispatch


class TestStructuredErrors:
    """Correct pattern: structured error context."""

    def test_timeout_has_error_type(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "web_researcher", "fetch_page",
            {"url": "https://timeout.example.com/remote-data"}, services,
        ))
        assert result["status"] == "error"
        assert result["error_type"] == "timeout"

    def test_timeout_is_retry_eligible(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "web_researcher", "fetch_page",
            {"url": "https://timeout.example.com/remote-data"}, services,
        ))
        assert result["retry_eligible"] is True

    def test_not_found_is_not_retry_eligible(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "web_researcher", "fetch_page",
            {"url": "https://healthtech.example.com/ai-revolution"}, services,
        ))
        assert result["retry_eligible"] is False

    def test_not_found_has_fallback(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "web_researcher", "fetch_page",
            {"url": "https://healthtech.example.com/ai-revolution"}, services,
        ))
        assert result["fallback_available"] is True

    def test_error_includes_source(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "web_researcher", "fetch_page",
            {"url": "https://timeout.example.com/remote-data"}, services,
        ))
        assert "timeout.example.com" in result["source"]

    def test_invalid_input_error(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "web_researcher", "search_web",
            {"query": ""}, services,
        ))
        assert result["status"] == "error"
        assert result["error_type"] == "invalid_input"


class TestSilentVsStructured:
    """Side-by-side comparison: silent failure vs structured error."""

    def test_timeout_comparison(self, services: ServiceContainer):
        """Structured error gives coordinator decision info; silent doesn't."""
        structured = json.loads(dispatch(
            "web_researcher", "fetch_page",
            {"url": "https://timeout.example.com/remote-data"}, services,
        ))
        silent = json.loads(handle_fetch_page_silent(
            {"url": "https://timeout.example.com/remote-data"}, services,
        ))

        # Structured: coordinator knows it was a timeout and can retry
        assert structured["status"] == "error"
        assert structured["error_type"] == "timeout"
        assert structured["retry_eligible"] is True

        # Silent: coordinator thinks the source had no data
        assert silent["status"] == "success"
        assert silent["data"] is None
        assert "error_type" not in silent
        assert "retry_eligible" not in silent

    def test_structured_error_has_all_fields(self, services: ServiceContainer):
        """Structured errors always include the full decision tree."""
        result = json.loads(dispatch(
            "web_researcher", "fetch_page",
            {"url": "https://timeout.example.com/remote-data"}, services,
        ))
        required_fields = {"status", "error_type", "source", "message", "retry_eligible", "fallback_available"}
        assert required_fields.issubset(result.keys())


class TestErrorsMatchModel:
    """Every emitted error must round-trip through ToolErrorResponse."""

    @pytest.mark.parametrize("agent_type,tool_name,input_dict", [
        ("web_researcher", "fetch_page", {"url": "https://timeout.example.com/remote-data"}),
        ("web_researcher", "fetch_page", {"url": "https://healthtech.example.com/ai-revolution"}),
        ("web_researcher", "search_web", {"query": ""}),
        ("document_analyzer", "parse_document", {"doc_id": "missing"}),
        ("data_extractor", "query_database", {"table": "missing"}),
        ("fact_checker", "verify_claim", {}),
        ("coordinator", "delegate_task", {"agent_type": "nope", "instruction": "x"}),
        ("web_researcher", "query_database", {}),
        ("nobody", "search_web", {}),
    ])
    def test_error_validates(self, services: ServiceContainer, agent_type, tool_name, input_dict):
        raw = dispatch(agent_type, tool_name, input_dict, services)
        parsed = ToolErrorResponse.model_validate_json(raw)
        assert parsed.status == "error"
