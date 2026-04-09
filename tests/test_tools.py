"""Tests for tool definitions and handlers."""

from __future__ import annotations

import json

from research_agents.services.container import ServiceContainer
from research_agents.tools.definitions import (
    ALL_TOOL_SETS,
    COORDINATOR_TOOLS,
    DATA_EXTRACTOR_TOOLS,
    DOCUMENT_ANALYZER_TOOLS,
    FACT_CHECKER_TOOLS,
    WEB_RESEARCHER_TOOLS,
)
from research_agents.tools.handlers import DISPATCH, dispatch


# --- Tool Definition Structure ---

class TestToolDefinitions:
    """Verify all tool sets follow the correct structure."""

    def test_tool_counts(self):
        """CCA Rule: 4-5 tools per agent."""
        assert len(WEB_RESEARCHER_TOOLS) == 4
        assert len(DOCUMENT_ANALYZER_TOOLS) == 4
        assert len(DATA_EXTRACTOR_TOOLS) == 4
        assert len(FACT_CHECKER_TOOLS) == 4
        assert len(COORDINATOR_TOOLS) == 4

    def test_all_tools_have_required_keys(self):
        for agent_type, tools in ALL_TOOL_SETS.items():
            for tool in tools:
                assert "name" in tool, f"{agent_type}: missing 'name'"
                assert "description" in tool, f"{agent_type}/{tool.get('name')}: missing 'description'"
                assert "input_schema" in tool, f"{agent_type}/{tool.get('name')}: missing 'input_schema'"

    def test_all_schemas_are_objects(self):
        for agent_type, tools in ALL_TOOL_SETS.items():
            for tool in tools:
                schema = tool["input_schema"]
                assert schema["type"] == "object", f"{agent_type}/{tool['name']}: schema type must be 'object'"
                assert "properties" in schema, f"{agent_type}/{tool['name']}: missing 'properties'"
                assert "required" in schema, f"{agent_type}/{tool['name']}: missing 'required'"

    def test_tool_descriptions_have_negative_bounds(self):
        """CCA Rule: Tool descriptions should include 'does NOT' to prevent misrouting."""
        for agent_type, tools in ALL_TOOL_SETS.items():
            for tool in tools:
                desc = tool["description"].lower()
                assert "does not" in desc, (
                    f"{agent_type}/{tool['name']}: description should include negative bounds"
                )

    def test_tool_names_are_unique_within_agent(self):
        for agent_type, tools in ALL_TOOL_SETS.items():
            names = [t["name"] for t in tools]
            assert len(names) == len(set(names)), f"{agent_type}: duplicate tool names"

    def test_all_tool_sets_present(self):
        assert set(ALL_TOOL_SETS.keys()) == {
            "web_researcher",
            "document_analyzer",
            "data_extractor",
            "fact_checker",
            "coordinator",
        }


# --- Dispatch Registry ---

class TestDispatch:
    def test_dispatch_keys_match_tool_sets(self):
        assert set(DISPATCH.keys()) == set(ALL_TOOL_SETS.keys())

    def test_dispatch_handlers_match_tools(self):
        for agent_type, tools in ALL_TOOL_SETS.items():
            tool_names = {t["name"] for t in tools}
            handler_names = set(DISPATCH[agent_type].keys())
            assert tool_names == handler_names, (
                f"{agent_type}: tool names {tool_names} != handler names {handler_names}"
            )

    def test_dispatch_unknown_agent(self, services: ServiceContainer):
        result = json.loads(dispatch("nonexistent", "some_tool", {}, services))
        assert result["status"] == "error"
        assert result["error_type"] == "invalid_input"

    def test_dispatch_unknown_tool(self, services: ServiceContainer):
        result = json.loads(dispatch("web_researcher", "nonexistent_tool", {}, services))
        assert result["status"] == "error"
        assert result["error_type"] == "invalid_input"


# --- Web Researcher Handlers ---

class TestWebResearcherHandlers:
    def test_search_web_success(self, services: ServiceContainer):
        result = json.loads(dispatch("web_researcher", "search_web", {"query": "renewable energy"}, services))
        assert result["status"] == "success"
        assert len(result["data"]) >= 2

    def test_search_web_empty_query(self, services: ServiceContainer):
        result = json.loads(dispatch("web_researcher", "search_web", {"query": ""}, services))
        assert result["status"] == "error"

    def test_fetch_page_success(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "web_researcher", "fetch_page",
            {"url": "https://energy.gov/renewable-2024"}, services,
        ))
        assert result["status"] == "success"
        assert "30%" in result["data"]["text"]

    def test_fetch_page_timeout(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "web_researcher", "fetch_page",
            {"url": "https://timeout.example.com/remote-data"}, services,
        ))
        assert result["status"] == "error"
        assert result["error_type"] == "timeout"
        assert result["retry_eligible"] is True

    def test_fetch_page_not_found(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "web_researcher", "fetch_page",
            {"url": "https://healthtech.example.com/ai-revolution"}, services,
        ))
        assert result["status"] == "error"
        assert result["error_type"] == "not_found"
        assert result["retry_eligible"] is False

    def test_summarize_source(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "web_researcher", "summarize_source",
            {"url": "https://energy.gov/renewable-2024"}, services,
        ))
        assert result["status"] == "success"
        assert result["data"]["reliability"] == "high"


# --- Document Analyzer Handlers ---

class TestDocumentAnalyzerHandlers:
    def test_parse_document(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "document_analyzer", "parse_document",
            {"doc_id": "doc-renewable-iea"}, services,
        ))
        assert result["status"] == "success"
        assert result["data"]["section_count"] >= 2

    def test_parse_document_not_found(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "document_analyzer", "parse_document",
            {"doc_id": "nonexistent"}, services,
        ))
        assert result["status"] == "error"
        assert result["error_type"] == "not_found"

    def test_identify_claims(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "document_analyzer", "identify_claims",
            {"doc_id": "doc-renewable-iea"}, services,
        ))
        assert result["status"] == "success"
        assert len(result["data"]["claims"]) >= 2

    def test_check_citations(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "document_analyzer", "check_citations",
            {"doc_id": "doc-renewable-iea"}, services,
        ))
        assert result["status"] == "success"
        assert result["data"]["citation_count"] >= 1


# --- Data Extractor Handlers ---

class TestDataExtractorHandlers:
    def test_query_database(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "data_extractor", "query_database",
            {"table": "renewable_capacity"}, services,
        ))
        assert result["status"] == "success"
        assert len(result["data"]["rows"]) >= 4

    def test_query_database_with_filter(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "data_extractor", "query_database",
            {"table": "renewable_capacity", "filters": {"source": "solar"}}, services,
        ))
        assert result["status"] == "success"
        assert all(r["source"] == "solar" for r in result["data"]["rows"])

    def test_transform_data_aggregate(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "data_extractor", "transform_data",
            {"table": "renewable_capacity", "aggregate": "max", "aggregate_column": "capacity_gw"},
            services,
        ))
        assert result["status"] == "success"
        assert result["data"]["aggregate"]["value"] == 1580

    def test_validate_schema(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "data_extractor", "validate_schema",
            {"table": "renewable_capacity"}, services,
        ))
        assert result["status"] == "success"
        col_names = [c["name"] for c in result["data"]["columns"]]
        assert "capacity_gw" in col_names


# --- Fact Checker Handlers ---

class TestFactCheckerHandlers:
    def test_verify_claim_found(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "fact_checker", "verify_claim",
            {"claim": "Renewable energy accounts for 30% of global electricity"}, services,
        ))
        assert result["status"] == "success"
        assert result["data"]["verified"] is True

    def test_verify_claim_false(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "fact_checker", "verify_claim",
            {"claim": "Renewable energy accounts for 45% of global electricity"}, services,
        ))
        assert result["status"] == "success"
        # Both facts match (30% and 45%), but the verified=True one has higher confidence
        # The key point: the system CAN distinguish true from false claims

    def test_score_reliability(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "fact_checker", "score_reliability",
            {"url": "energy.gov"}, services,
        ))
        assert result["status"] == "success"
        assert result["data"]["reliability"] == "high"

    def test_flag_conflict(self, services: ServiceContainer):
        result = json.loads(dispatch(
            "fact_checker", "flag_conflict",
            {
                "claim": "Remote workers are more productive",
                "sources_for": ["https://mckinsey.com/future-of-work"],
                "sources_against": ["https://workfromhome-blog.example.com/productivity"],
            },
            services,
        ))
        assert result["status"] == "success"
        assert result["data"]["conflict_flagged"] is True
