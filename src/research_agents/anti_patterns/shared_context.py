"""Anti-pattern: Shared context between coordinator and subagents.

CCA Exam: Subagents do NOT inherit coordinator context. If the coordinator
has citation format rules in its context but doesn't explicitly include
them in the delegation message, the subagent has no knowledge of them.

This module passes the coordinator's full messages list to subagents
instead of using explicit context passing.
"""

from __future__ import annotations

from research_agents.agent.agent_loop import AgentResult, run_agent_loop
from research_agents.agent.subagents import SUBAGENT_CONFIGS
from research_agents.services.container import ServiceContainer


def run_leaky_subagent(
    client: object,
    services: ServiceContainer,
    coordinator_messages: list[dict],
    agent_type: str,
    model: str = "claude-sonnet-4-6",
) -> AgentResult:
    """ANTI-PATTERN: Passes coordinator's full message history to subagent.

    Problems:
    - Token waste: subagent processes entire coordinator conversation
    - Context pollution: web researcher sees document analysis instructions
    - Attention dilution: useful context buried in irrelevant messages
    - No isolation: subagent sees other subagents' results

    The correct approach is build_subagent_context() which passes ONLY
    explicitly selected context via SubTask.
    """
    config = SUBAGENT_CONFIGS.get(agent_type)
    if config is None:
        return AgentResult(content=f"Unknown agent: {agent_type}")

    # WRONG: dumps entire coordinator history as the user message
    leaked_context = str(coordinator_messages)

    return run_agent_loop(
        client=client,
        services=services,
        user_message=leaked_context,  # ANTI-PATTERN: full history leaked
        system_prompt=config.system_prompt,
        tools=config.tools,
        agent_type=agent_type,
        model=model,
    )
