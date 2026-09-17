"""Anti-pattern: Super Agent with every tool (20 here; the exam's threshold is 18+).

CCA Exam: When an agent has 18 or more tools, a significant portion of
attention goes to evaluating tool descriptions instead of the actual task.
Similar tools create ambiguity and misrouting.

The correct answer is ALWAYS to decompose into specialized subagents
with 4-5 tools each. Better descriptions don't fix the structural problem.
"""

from __future__ import annotations

from research_agents.services.container import ServiceContainer
from research_agents.tools._errors import error_response
from research_agents.tools.definitions import (
    COORDINATOR_TOOLS,
    DATA_EXTRACTOR_TOOLS,
    DOCUMENT_ANALYZER_TOOLS,
    FACT_CHECKER_TOOLS,
    WEB_RESEARCHER_TOOLS,
)
from research_agents.tools.handlers import DISPATCH, Handler

# Combine ALL tool sets into one giant list — the super agent anti-pattern
SUPER_AGENT_TOOLS: list[dict] = (
    WEB_RESEARCHER_TOOLS
    + DOCUMENT_ANALYZER_TOOLS
    + DATA_EXTRACTOR_TOOLS
    + FACT_CHECKER_TOOLS
    + COORDINATOR_TOOLS
)

SUPER_AGENT_PROMPT = """\
You are a universal research agent. You have access to ALL tools:
web search, document parsing, data extraction, fact checking, and coordination.

Use whatever tools you need to answer the research query.
"""


def get_super_agent_tool_count() -> int:
    """Return the number of tools in the super agent (for notebook demos)."""
    return len(SUPER_AGENT_TOOLS)


# Flat name -> handler map: every tool from every agent, no scoping.
SUPER_AGENT_DISPATCH: dict[str, Handler] = {
    tool_name: handler
    for handlers in DISPATCH.values()
    for tool_name, handler in handlers.items()
}


def super_agent_dispatch(
    agent_type: str, tool_name: str, input_dict: dict, services: ServiceContainer
) -> str:
    """ANTI-PATTERN router: executes any tool for any caller.

    ``agent_type`` is accepted only so the signature matches
    ``tools.handlers.dispatch`` and can be injected into
    ``run_agent_loop(dispatch_fn=...)``; it is ignored. A web researcher that
    decides to call ``query_database`` simply gets the database.
    """
    handler = SUPER_AGENT_DISPATCH.get(tool_name)
    if handler is None:
        return error_response("invalid_input", "dispatch", f"Unknown tool: {tool_name}")
    return handler(input_dict, services)
