"""Dispatch registry for tool handlers.

Nested ``DISPATCH[agent_type][tool_name]`` so handlers are isolated per
agent: a tool name is only reachable through the agent that owns it, and an
out-of-scope call gets a structured ``invalid_input`` error rather than a
handler. Follows the same dict-based dispatch pattern as the sibling project.
"""

from __future__ import annotations

from collections.abc import Callable

from research_agents.services.container import ServiceContainer
from research_agents.tools._errors import error_response
from research_agents.tools.coordinator_tools import (
    handle_collect_results,
    handle_compile_report,
    handle_delegate_task,
    handle_resolve_conflicts,
)
from research_agents.tools.data_extractor import (
    handle_format_output,
    handle_query_database,
    handle_transform_data,
    handle_validate_schema,
)
from research_agents.tools.document_analyzer import (
    handle_check_citations,
    handle_extract_sections,
    handle_identify_claims,
    handle_parse_document,
)
from research_agents.tools.fact_checker import (
    handle_cross_reference,
    handle_flag_conflict,
    handle_score_reliability,
    handle_verify_claim,
)
from research_agents.tools.web_researcher import (
    handle_extract_text,
    handle_fetch_page,
    handle_search_web,
    handle_summarize_source,
)

# Type alias for handler functions
Handler = Callable[[dict, ServiceContainer], str]

# Nested dispatch: DISPATCH[agent_type][tool_name] -> handler function
DISPATCH: dict[str, dict[str, Handler]] = {
    "web_researcher": {
        "search_web": handle_search_web,
        "fetch_page": handle_fetch_page,
        "extract_text": handle_extract_text,
        "summarize_source": handle_summarize_source,
    },
    "document_analyzer": {
        "parse_document": handle_parse_document,
        "extract_sections": handle_extract_sections,
        "identify_claims": handle_identify_claims,
        "check_citations": handle_check_citations,
    },
    "data_extractor": {
        "query_database": handle_query_database,
        "transform_data": handle_transform_data,
        "validate_schema": handle_validate_schema,
        "format_output": handle_format_output,
    },
    "fact_checker": {
        "verify_claim": handle_verify_claim,
        "cross_reference": handle_cross_reference,
        "score_reliability": handle_score_reliability,
        "flag_conflict": handle_flag_conflict,
    },
    "coordinator": {
        "delegate_task": handle_delegate_task,
        "collect_results": handle_collect_results,
        "resolve_conflicts": handle_resolve_conflicts,
        "compile_report": handle_compile_report,
    },
}


def dispatch(agent_type: str, tool_name: str, input_dict: dict, services: ServiceContainer) -> str:
    """Route a tool call to the correct handler.

    Returns a JSON string — always. On dispatch errors, returns a structured
    error response (never raises).
    """
    agent_handlers = DISPATCH.get(agent_type)
    if agent_handlers is None:
        return error_response(
            "invalid_input",
            "dispatch",
            f"Unknown agent_type: {agent_type}",
        )
    handler = agent_handlers.get(tool_name)
    if handler is None:
        return error_response(
            "invalid_input",
            "dispatch",
            f"Unknown tool '{tool_name}' for agent '{agent_type}'",
        )
    return handler(input_dict, services)
