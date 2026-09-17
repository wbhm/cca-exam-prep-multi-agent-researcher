"""Tests for anti-pattern modules.

These tests verify that anti-patterns are wrong in the RIGHT way —
they demonstrate specific CCA failures for notebook comparisons.
"""

from __future__ import annotations

import json

from research_agents.anti_patterns.silent_failures import (
    SILENT_DISPATCH,
    handle_fetch_page_silent,
    handle_search_web_silent,
)
from research_agents.anti_patterns.super_agent import (
    SUPER_AGENT_PROMPT,
    SUPER_AGENT_TOOLS,
    get_super_agent_tool_count,
)
from research_agents.services.container import ServiceContainer
from research_agents.tools.definitions import (
    ALL_TOOL_SETS,
    WEB_RESEARCHER_TOOLS,
)


class TestSuperAgentAntiPattern:
    def test_has_18_plus_tools(self):
        """CCA Rule: 18 tools fails. Super agent has all tools combined."""
        assert get_super_agent_tool_count() >= 18

    def test_contains_all_correct_tools(self):
        """All correct tool sets should appear in the super agent."""
        super_names = {t["name"] for t in SUPER_AGENT_TOOLS}
        for agent_type, tools in ALL_TOOL_SETS.items():
            for tool in tools:
                assert tool["name"] in super_names, (
                    f"Super agent missing {agent_type}/{tool['name']}"
                )

    def test_each_tool_has_required_keys(self):
        for tool in SUPER_AGENT_TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool

    def test_prompt_is_generic(self):
        """Super agent prompt doesn't focus on any specialty."""
        assert "universal" in SUPER_AGENT_PROMPT.lower() or "all tools" in SUPER_AGENT_PROMPT.lower()

    def test_correct_agents_have_fewer_tools(self):
        """Each correct agent has 4-5 tools, not 18+."""
        for agent_type, tools in ALL_TOOL_SETS.items():
            assert len(tools) <= 5, f"{agent_type}: {len(tools)} tools"
            assert len(tools) >= 3, f"{agent_type}: {len(tools)} tools"


class TestSilentFailureAntiPattern:
    def test_search_returns_success_on_empty(self, services: ServiceContainer):
        """Silent failure returns success even when search finds nothing."""
        result = json.loads(handle_search_web_silent({"query": "nonexistent xyz"}, services))
        assert result["status"] == "success"
        # data is an empty list (no results), but status is still "success"

    def test_fetch_returns_success_on_timeout(self, services: ServiceContainer):
        """ANTI-PATTERN: Timeout returns success with null."""
        result = json.loads(
            handle_fetch_page_silent(
                {"url": "https://timeout.example.com/remote-data"}, services,
            )
        )
        assert result["status"] == "success"
        assert result["data"] is None  # The coordinator can't tell this was an error

    def test_fetch_returns_success_on_404(self, services: ServiceContainer):
        """ANTI-PATTERN: 404 returns success with null."""
        result = json.loads(
            handle_fetch_page_silent(
                {"url": "https://healthtech.example.com/ai-revolution"}, services,
            )
        )
        assert result["status"] == "success"
        assert result["data"] is None

    def test_cannot_distinguish_error_from_empty(self, services: ServiceContainer):
        """The whole problem: timeout and 'no data' look identical."""
        timeout_result = json.loads(
            handle_fetch_page_silent(
                {"url": "https://timeout.example.com/remote-data"}, services,
            )
        )
        # Compare with a made-up URL that just doesn't exist
        missing_result = json.loads(
            handle_fetch_page_silent(
                {"url": "https://totally-unknown.example.com"}, services,
            )
        )
        # Both return identical responses — the coordinator can't tell them apart
        assert timeout_result == missing_result

    def test_silent_dispatch_exists(self):
        assert "web_researcher" in SILENT_DISPATCH


class TestSharedContextAntiPattern:
    def test_leaky_function_exists(self):
        """Verify the anti-pattern module is importable."""
        from research_agents.anti_patterns.shared_context import run_leaky_subagent  # noqa: F401

    def test_leaky_context_is_string_of_messages(self):
        """The anti-pattern converts messages list to string (wasteful)."""
        from research_agents.anti_patterns.shared_context import run_leaky_subagent
        # The function signature takes coordinator_messages as list[dict]
        # and converts it to str() — this is the anti-pattern
        import inspect

        sig = inspect.signature(run_leaky_subagent)
        params = list(sig.parameters.keys())
        assert "coordinator_messages" in params


class TestRunnableAntiPatterns:
    """Anti-patterns must be runnable through the real loop so notebooks can measure them."""

    def test_silent_dispatch_hides_timeout(self, services: ServiceContainer):
        from research_agents.anti_patterns.silent_failures import silent_dispatch

        result = json.loads(silent_dispatch(
            "web_researcher", "fetch_page",
            {"url": "https://timeout.example.com/remote-data"}, services,
        ))
        assert result == {"status": "success", "data": None}

    def test_silent_dispatch_falls_back_to_real_handlers(self, services: ServiceContainer):
        from research_agents.anti_patterns.silent_failures import silent_dispatch

        result = json.loads(silent_dispatch(
            "fact_checker", "score_reliability", {"url": "energy.gov"}, services,
        ))
        assert result["data"]["reliability"] == "high"

    def test_super_agent_dispatch_ignores_scoping(self, services: ServiceContainer):
        """The super agent executes any tool for any caller; scoped dispatch refuses."""
        from research_agents.anti_patterns.super_agent import super_agent_dispatch
        from research_agents.tools.handlers import dispatch

        args = ("web_researcher", "query_database", {"table": "remote_work_stats"}, services)
        scoped = json.loads(dispatch(*args))
        unscoped = json.loads(super_agent_dispatch(*args))
        assert scoped["status"] == "error"
        assert scoped["error_type"] == "invalid_input"
        assert unscoped["status"] == "success"
        assert unscoped["data"]["table"] == "remote_work_stats"

    def test_super_agent_has_exactly_20_tools(self):
        assert get_super_agent_tool_count() == 20
