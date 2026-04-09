"""Tests for context isolation — the #1 CCA concept.

These tests verify that subagents receive ONLY explicit context,
never the coordinator's messages, system prompt, or other subagent results.
"""

from __future__ import annotations

from research_agents.agent.agent_loop import AgentResult
from research_agents.agent.context_builder import build_subagent_context
from research_agents.agent.subagents import SUBAGENT_CONFIGS
from research_agents.models.research import SubTask


class TestBuildSubagentContext:
    """Test that context_builder enforces isolation."""

    def test_returns_string_not_list(self):
        """CCA Rule: Subagent input is a string, not a messages list."""
        task = SubTask(
            task_id="t1",
            agent_type="web_researcher",
            instruction="Search for renewable energy",
            context="Focus on 2024 data",
        )
        result = build_subagent_context(task)
        assert isinstance(result, str)

    def test_includes_instruction(self):
        task = SubTask(
            task_id="t1",
            agent_type="web_researcher",
            instruction="Search for renewable energy stats",
            context="",
        )
        result = build_subagent_context(task)
        assert "Search for renewable energy stats" in result

    def test_includes_explicit_context(self):
        task = SubTask(
            task_id="t1",
            agent_type="web_researcher",
            instruction="Search",
            context="Focus on IEA 2024 report data",
        )
        result = build_subagent_context(task)
        assert "IEA 2024" in result

    def test_no_context_when_empty(self):
        task = SubTask(
            task_id="t1",
            agent_type="web_researcher",
            instruction="Search",
            context="",
        )
        result = build_subagent_context(task)
        assert "## Context" not in result

    def test_includes_predecessor_results_for_depends_on(self):
        predecessor = AgentResult(content="Found 3 sources about renewables.")
        task = SubTask(
            task_id="t2",
            agent_type="fact_checker",
            instruction="Verify these claims",
            context="",
            depends_on=["t1"],
        )
        result = build_subagent_context(task, predecessor_results={"t1": predecessor})
        assert "Found 3 sources about renewables" in result

    def test_excludes_non_dependency_results(self):
        """CCA Rule: Only depends_on results are included."""
        t1_result = AgentResult(content="Web search results")
        t2_result = AgentResult(content="Document analysis results")
        task = SubTask(
            task_id="t3",
            agent_type="fact_checker",
            instruction="Verify",
            context="",
            depends_on=["t1"],  # Only depends on t1, NOT t2
        )
        result = build_subagent_context(
            task,
            predecessor_results={"t1": t1_result, "t2": t2_result},
        )
        assert "Web search results" in result
        assert "Document analysis results" not in result

    def test_no_predecessor_section_without_depends_on(self):
        """Tasks with no dependencies get no predecessor results."""
        t1_result = AgentResult(content="Should not appear")
        task = SubTask(
            task_id="t2",
            agent_type="web_researcher",
            instruction="Search independently",
            context="",
            depends_on=[],
        )
        result = build_subagent_context(task, predecessor_results={"t1": t1_result})
        assert "Should not appear" not in result
        assert "## Prior Results" not in result


class TestSubagentConfigIsolation:
    """Verify subagent configs enforce isolation by design."""

    def test_each_agent_has_own_system_prompt(self):
        prompts = {cfg.system_prompt for cfg in SUBAGENT_CONFIGS.values()}
        assert len(prompts) == len(SUBAGENT_CONFIGS), "Each agent must have a unique prompt"

    def test_each_agent_has_own_tools(self):
        tool_sets = [tuple(t["name"] for t in cfg.tools) for cfg in SUBAGENT_CONFIGS.values()]
        assert len(set(tool_sets)) == len(SUBAGENT_CONFIGS), "Each agent must have unique tools"

    def test_no_agent_has_more_than_5_tools(self):
        """CCA Rule: 4-5 tools per agent."""
        for agent_type, cfg in SUBAGENT_CONFIGS.items():
            assert len(cfg.tools) <= 5, f"{agent_type} has {len(cfg.tools)} tools (max 5)"
            assert len(cfg.tools) >= 3, f"{agent_type} has {len(cfg.tools)} tools (min 3)"

    def test_web_researcher_prompt_mentions_limitations(self):
        cfg = SUBAGENT_CONFIGS["web_researcher"]
        assert "do not" in cfg.system_prompt.lower()

    def test_all_expected_agents_present(self):
        assert set(SUBAGENT_CONFIGS.keys()) == {
            "web_researcher",
            "document_analyzer",
            "data_extractor",
            "fact_checker",
        }
