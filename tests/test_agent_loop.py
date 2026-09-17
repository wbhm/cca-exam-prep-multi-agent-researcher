"""Tests for the agentic tool-use loop."""

from __future__ import annotations

import json
from types import SimpleNamespace

from research_agents.agent.agent_loop import AgentResult, UsageSummary, run_agent_loop
from research_agents.services.container import ServiceContainer


def _make_text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def _make_tool_use_block(tool_id: str, name: str, input_dict: dict) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=tool_id, name=name, input=input_dict)


def _make_response(
    content: list, stop_reason: str = "end_turn", usage: dict | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        content=content,
        stop_reason=stop_reason,
        usage=SimpleNamespace(**(usage or {"input_tokens": 100, "output_tokens": 50})),
    )


class TestUsageSummary:
    def test_add(self):
        u = UsageSummary()
        u.add({"input_tokens": 100, "output_tokens": 50})
        u.add({"input_tokens": 200, "output_tokens": 100})
        assert u.input_tokens == 300
        assert u.output_tokens == 150


class TestAgentLoop:
    def test_single_turn_end(self, services: ServiceContainer):
        """Agent responds with text and ends."""
        mock_client = SimpleNamespace(
            messages=SimpleNamespace(
                create=lambda **kwargs: _make_response(
                    [_make_text_block("Final answer.")],
                    stop_reason="end_turn",
                )
            )
        )
        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="Test query",
            system_prompt="You are a test agent.",
            tools=[],
            agent_type="web_researcher",
        )
        assert result.content == "Final answer."
        assert result.iterations == 1
        assert result.tool_calls == 0

    def test_tool_use_then_end(self, services: ServiceContainer):
        """Agent calls a tool, gets result, then ends."""
        call_count = 0

        def mock_create(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_response(
                    [_make_tool_use_block("t1", "search_web", {"query": "renewable energy"})],
                    stop_reason="tool_use",
                )
            return _make_response(
                [_make_text_block("Found 3 results about renewable energy.")],
                stop_reason="end_turn",
            )

        mock_client = SimpleNamespace(
            messages=SimpleNamespace(create=mock_create)
        )
        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="Search for renewable energy",
            system_prompt="You are a web researcher.",
            tools=[{"name": "search_web"}],
            agent_type="web_researcher",
        )
        assert result.content == "Found 3 results about renewable energy."
        assert result.iterations == 2
        assert result.tool_calls == 1

    def test_max_iterations_safety(self, services: ServiceContainer):
        """Loop stops at max_iterations even if tool_use continues."""
        mock_client = SimpleNamespace(
            messages=SimpleNamespace(
                create=lambda **kwargs: _make_response(
                    [_make_tool_use_block("t1", "search_web", {"query": "test"})],
                    stop_reason="tool_use",
                )
            )
        )
        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="Infinite loop test",
            system_prompt="Test",
            tools=[{"name": "search_web"}],
            agent_type="web_researcher",
            max_iterations=3,
        )
        assert result.iterations == 3
        assert result.tool_calls == 3

    def test_usage_accumulates(self, services: ServiceContainer):
        """Usage tokens are summed across iterations."""
        call_count = 0

        def mock_create(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_response(
                    [_make_tool_use_block("t1", "search_web", {"query": "test"})],
                    stop_reason="tool_use",
                    usage={"input_tokens": 100, "output_tokens": 50},
                )
            return _make_response(
                [_make_text_block("Done")],
                stop_reason="end_turn",
                usage={"input_tokens": 200, "output_tokens": 100},
            )

        mock_client = SimpleNamespace(
            messages=SimpleNamespace(create=mock_create)
        )
        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="Test",
            system_prompt="Test",
            tools=[{"name": "search_web"}],
            agent_type="web_researcher",
        )
        assert result.usage.input_tokens == 300
        assert result.usage.output_tokens == 150


class TestStopReasons:
    """The loop must exit on every non-tool_use stop reason and record it."""

    def test_max_tokens_stops_after_one_iteration(self, services: ServiceContainer):
        """A truncated response must not be re-sent as if it were a tool call."""
        mock_client = SimpleNamespace(
            messages=SimpleNamespace(
                create=lambda **kwargs: _make_response(
                    [_make_text_block("Partial ans")], stop_reason="max_tokens",
                )
            )
        )
        result = run_agent_loop(
            client=mock_client, services=services, user_message="q",
            system_prompt="s", tools=[], agent_type="web_researcher", max_iterations=5,
        )
        assert result.iterations == 1
        assert result.stop_reason == "max_tokens"
        assert result.content == "Partial ans"

    def test_end_turn_records_stop_reason(self, services: ServiceContainer):
        mock_client = SimpleNamespace(
            messages=SimpleNamespace(
                create=lambda **kwargs: _make_response([_make_text_block("Done")])
            )
        )
        result = run_agent_loop(
            client=mock_client, services=services, user_message="q",
            system_prompt="s", tools=[], agent_type="web_researcher",
        )
        assert result.stop_reason == "end_turn"

    def test_exhausted_loop_is_marked(self, services: ServiceContainer):
        """Hitting max_iterations must be distinguishable from a clean finish."""
        mock_client = SimpleNamespace(
            messages=SimpleNamespace(
                create=lambda **kwargs: _make_response(
                    [_make_tool_use_block("t1", "search_web", {"query": "test"})],
                    stop_reason="tool_use",
                )
            )
        )
        result = run_agent_loop(
            client=mock_client, services=services, user_message="q",
            system_prompt="s", tools=[], agent_type="web_researcher", max_iterations=2,
        )
        assert result.stop_reason == "max_iterations"


class TestToolResults:
    def _client_calling(self, tool_name: str, tool_input: dict) -> SimpleNamespace:
        call_count = 0

        def mock_create(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_response(
                    [_make_tool_use_block("t1", tool_name, tool_input)], stop_reason="tool_use",
                )
            return _make_response([_make_text_block("Done")])

        return SimpleNamespace(messages=SimpleNamespace(create=mock_create))

    def test_tool_results_are_recorded(self, services: ServiceContainer):
        client = self._client_calling("fetch_page", {"url": "https://timeout.example.com/remote-data"})
        result = run_agent_loop(
            client=client, services=services, user_message="q",
            system_prompt="s", tools=[], agent_type="web_researcher",
        )
        assert len(result.tool_results) == 1
        entry = result.tool_results[0]
        assert entry["tool_name"] == "fetch_page"
        assert entry["tool_input"] == {"url": "https://timeout.example.com/remote-data"}
        assert json.loads(entry["result"])["error_type"] == "timeout"

    def test_error_results_are_flagged_is_error(self, services: ServiceContainer):
        """A structured error is also marked at the protocol level."""
        client = self._client_calling("fetch_page", {"url": "https://timeout.example.com/remote-data"})
        result = run_agent_loop(
            client=client, services=services, user_message="q",
            system_prompt="s", tools=[], agent_type="web_researcher",
        )
        tool_result_block = result.messages[2]["content"][0]
        assert tool_result_block["type"] == "tool_result"
        assert tool_result_block["is_error"] is True

    def test_success_results_are_not_flagged(self, services: ServiceContainer):
        client = self._client_calling("search_web", {"query": "renewable energy"})
        result = run_agent_loop(
            client=client, services=services, user_message="q",
            system_prompt="s", tools=[], agent_type="web_researcher",
        )
        assert result.messages[2]["content"][0]["is_error"] is False

    def test_dispatch_fn_is_injectable(self, services: ServiceContainer):
        seen = []

        def fake_dispatch(agent_type, tool_name, input_dict, svc):
            seen.append((agent_type, tool_name))
            return json.dumps({"status": "success", "data": "stub"})

        client = self._client_calling("search_web", {"query": "x"})
        result = run_agent_loop(
            client=client, services=services, user_message="q",
            system_prompt="s", tools=[], agent_type="web_researcher",
            dispatch_fn=fake_dispatch,
        )
        assert seen == [("web_researcher", "search_web")]
        assert json.loads(result.tool_results[0]["result"])["data"] == "stub"
