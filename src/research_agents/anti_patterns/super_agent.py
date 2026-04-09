"""Anti-pattern: Super Agent with 18+ tools.

CCA Exam: When an agent has 18 tools, a significant portion of attention
goes to evaluating tool descriptions instead of the actual task.
Similar tools create ambiguity and misrouting.

The correct answer is ALWAYS to decompose into specialized subagents
with 4-5 tools each. Better descriptions don't fix the structural problem.
"""

from __future__ import annotations

from research_agents.tools.definitions import (
    COORDINATOR_TOOLS,
    DATA_EXTRACTOR_TOOLS,
    DOCUMENT_ANALYZER_TOOLS,
    FACT_CHECKER_TOOLS,
    WEB_RESEARCHER_TOOLS,
)

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
