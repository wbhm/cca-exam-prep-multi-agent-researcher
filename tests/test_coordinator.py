"""Tests for the hub-and-spoke coordinator."""

from __future__ import annotations

from types import SimpleNamespace

from research_agents.agent.coordinator import (
    build_research_report,
    run_coordinator,
    sort_tasks_into_waves,
)
from research_agents.agent.agent_loop import AgentResult
from research_agents.models.research import SourceReliability, SubTask
from research_agents.services.container import ServiceContainer


def _make_text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def _make_response(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        content=[_make_text_block(text)],
        stop_reason="end_turn",
        usage=SimpleNamespace(input_tokens=100, output_tokens=50),
    )


class TestSortTasksIntoWaves:
    def test_parallel_tasks(self):
        """Tasks with no dependencies form one wave."""
        tasks = [
            SubTask(task_id="t1", agent_type="web_researcher", instruction="a", context=""),
            SubTask(task_id="t2", agent_type="document_analyzer", instruction="b", context=""),
        ]
        waves = sort_tasks_into_waves(tasks)
        assert len(waves) == 1
        assert len(waves[0]) == 2

    def test_sequential_tasks(self):
        """Tasks with dependencies form separate waves."""
        tasks = [
            SubTask(task_id="t1", agent_type="web_researcher", instruction="a", context=""),
            SubTask(
                task_id="t2", agent_type="fact_checker",
                instruction="b", context="", depends_on=["t1"],
            ),
        ]
        waves = sort_tasks_into_waves(tasks)
        assert len(waves) == 2
        assert waves[0][0].task_id == "t1"
        assert waves[1][0].task_id == "t2"

    def test_mixed_parallel_and_sequential(self):
        """Some tasks parallel, some sequential."""
        tasks = [
            SubTask(task_id="t1", agent_type="web_researcher", instruction="a", context=""),
            SubTask(task_id="t2", agent_type="data_extractor", instruction="b", context=""),
            SubTask(
                task_id="t3", agent_type="fact_checker",
                instruction="c", context="", depends_on=["t1", "t2"],
            ),
        ]
        waves = sort_tasks_into_waves(tasks)
        assert len(waves) == 2
        assert {t.task_id for t in waves[0]} == {"t1", "t2"}
        assert waves[1][0].task_id == "t3"

    def test_three_wave_chain(self):
        tasks = [
            SubTask(task_id="t1", agent_type="web_researcher", instruction="a", context=""),
            SubTask(
                task_id="t2", agent_type="fact_checker",
                instruction="b", context="", depends_on=["t1"],
            ),
            SubTask(
                task_id="t3", agent_type="document_analyzer",
                instruction="c", context="", depends_on=["t2"],
            ),
        ]
        waves = sort_tasks_into_waves(tasks)
        assert len(waves) == 3


class TestRunCoordinator:
    def test_delegates_to_correct_agents(self, services: ServiceContainer):
        """Coordinator delegates each task to the right agent type."""
        captured_calls = []

        def mock_create(**kwargs):
            captured_calls.append(kwargs)
            return _make_response("Agent result")

        mock_client = SimpleNamespace(
            messages=SimpleNamespace(create=mock_create)
        )
        tasks = [
            SubTask(task_id="t1", agent_type="web_researcher", instruction="search", context="ctx"),
            SubTask(task_id="t2", agent_type="data_extractor", instruction="query", context="ctx"),
        ]
        results, waves = run_coordinator(mock_client, services, tasks)
        assert len(results) == 2
        assert "t1" in results
        assert "t2" in results
        assert len(waves) == 1  # Both parallel

    def test_passes_explicit_context_only(self, services: ServiceContainer):
        """Verify subagent receives explicit context, not coordinator state."""
        captured_messages = []

        def mock_create(**kwargs):
            captured_messages.append(kwargs.get("messages", []))
            return _make_response("Done")

        mock_client = SimpleNamespace(
            messages=SimpleNamespace(create=mock_create)
        )
        tasks = [
            SubTask(
                task_id="t1",
                agent_type="web_researcher",
                instruction="Search for data",
                context="Focus on 2024 reports only",
            ),
        ]
        run_coordinator(mock_client, services, tasks)

        # The first message to the subagent should be a user message
        assert len(captured_messages) >= 1
        first_call = captured_messages[0]
        assert first_call[0]["role"] == "user"
        user_content = first_call[0]["content"]
        assert isinstance(user_content, str)
        assert "Search for data" in user_content
        assert "2024 reports" in user_content

    def test_sequential_tasks_get_predecessor_results(self, services: ServiceContainer):
        """Wave-2 tasks receive results from wave-1 via context builder."""
        call_count = 0

        def mock_create(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_response("Found 3 web sources")
            return _make_response("Verified claims")

        mock_client = SimpleNamespace(
            messages=SimpleNamespace(create=mock_create)
        )
        tasks = [
            SubTask(task_id="t1", agent_type="web_researcher", instruction="search", context=""),
            SubTask(
                task_id="t2", agent_type="fact_checker",
                instruction="verify", context="", depends_on=["t1"],
            ),
        ]
        results, waves = run_coordinator(mock_client, services, tasks)
        assert len(waves) == 2
        assert results["t1"].content == "Found 3 web sources"
        assert results["t2"].content == "Verified claims"

    def test_unknown_agent_type(self, services: ServiceContainer):
        mock_client = SimpleNamespace(
            messages=SimpleNamespace(create=lambda **kw: _make_response("x"))
        )
        tasks = [
            SubTask(task_id="t1", agent_type="nonexistent", instruction="x", context=""),
        ]
        results, _ = run_coordinator(mock_client, services, tasks)
        assert "Error" in results["t1"].content


class TestBuildResearchReport:
    def test_basic_report(self):
        results = {
            "t1": AgentResult(content="Found renewable energy data."),
            "t2": AgentResult(content="Verified 2 claims."),
        }
        report = build_research_report(
            query="renewable energy",
            results=results,
            reliability_lookup={},
        )
        assert report.query == "renewable energy"
        assert len(report.findings) == 2
        assert report.confidence_score > 0

    def test_report_with_gaps(self):
        results = {"t1": AgentResult(content="Partial data.")}
        report = build_research_report(
            query="test",
            results=results,
            reliability_lookup={},
            gaps=["Source X was unavailable", "Source Y timed out"],
        )
        assert len(report.gaps) == 2
        assert report.confidence_score < 0.8  # Reduced by gaps

    def test_report_with_conflicts(self):
        results = {"t1": AgentResult(content="Mixed results.")}
        report = build_research_report(
            query="test",
            results=results,
            reliability_lookup={"https://a.com": SourceReliability.HIGH, "https://b.com": SourceReliability.LOW},
            conflicts=[{
                "claim": "X is true",
                "sources_for": ["https://a.com"],
                "sources_against": ["https://b.com"],
            }],
        )
        assert len(report.conflicts) == 1
        assert report.conflicts[0].resolution == "highest_reliability"
