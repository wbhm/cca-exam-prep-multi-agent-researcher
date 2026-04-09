"""Import smoke tests — verify all public modules are importable."""

from __future__ import annotations


class TestImports:
    def test_top_level(self):
        import research_agents
        assert hasattr(research_agents, "__version__")

    def test_models_research(self):
        from research_agents.models.research import (
            ConflictRecord,
            Document,
            FactRecord,
            ResearchQuery,
            ResearchReport,
            SearchResult,
            SourceReliability,
            SourceResult,
            SubTask,
        )

    def test_models_errors(self):
        from research_agents.models.errors import SilentFailureResponse, ToolErrorResponse

    def test_services(self):
        from research_agents.services.container import ServiceContainer
        from research_agents.services.database import DatabaseService
        from research_agents.services.document_store import DocumentStore
        from research_agents.services.knowledge_base import KnowledgeBase
        from research_agents.services.web_search import WebSearchService

    def test_tools(self):
        from research_agents.tools.definitions import (
            ALL_TOOL_SETS,
            COORDINATOR_TOOLS,
            DATA_EXTRACTOR_TOOLS,
            DOCUMENT_ANALYZER_TOOLS,
            FACT_CHECKER_TOOLS,
            WEB_RESEARCHER_TOOLS,
        )
        from research_agents.tools.handlers import DISPATCH, dispatch

    def test_agent(self):
        from research_agents.agent.agent_loop import AgentResult, UsageSummary, run_agent_loop
        from research_agents.agent.context_builder import build_subagent_context
        from research_agents.agent.coordinator import run_coordinator, sort_tasks_into_waves
        from research_agents.agent.subagents import SUBAGENT_CONFIGS

    def test_anti_patterns(self):
        from research_agents.anti_patterns.super_agent import SUPER_AGENT_TOOLS
        from research_agents.anti_patterns.shared_context import run_leaky_subagent
        from research_agents.anti_patterns.silent_failures import SILENT_DISPATCH

    def test_data(self):
        from research_agents.data.sources import SEARCH_INDEX, DOCUMENTS, DATABASE_TABLES
        from research_agents.data.scenarios import SCENARIOS
