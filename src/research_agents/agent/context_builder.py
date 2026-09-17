"""Explicit context passing — the enforcer of context isolation.

CCA Key Concept #1: Subagents do NOT inherit coordinator context.
This module is the only way ``run_coordinator`` builds subagent input. It
accepts a SubTask (which has only explicitly-selected context) and optionally
predecessor results (filtered by depends_on). It returns a plain string.
(``run_agent_loop`` itself accepts any string; the anti-pattern in
``anti_patterns/shared_context.py`` exploits exactly that.)

The coordinator's message history, system prompt, and other subagents'
results are NEVER passed unless deliberately included in the SubTask.
"""

from __future__ import annotations

from research_agents.agent.agent_loop import AgentResult
from research_agents.models.research import SubTask


def build_subagent_context(
    task: SubTask,
    predecessor_results: dict[str, AgentResult] | None = None,
) -> str:
    """Build the ONLY context a subagent sees.

    The subagent receives:
    - task.instruction (what to do)
    - task.context (explicitly selected facts from coordinator)
    - Predecessor results filtered to task.depends_on (if sequential)

    The subagent does NOT receive:
    - Coordinator's messages list
    - Coordinator's system prompt
    - Other subagents' results (unless in depends_on)
    - The original research query (unless coordinator chose to include it)

    Returns:
        A plain string — the complete context for the subagent.
    """
    parts: list[str] = []

    # 1. Task instruction (always present)
    parts.append(f"## Task\n{task.instruction}")

    # 2. Explicit context from coordinator (may be empty)
    if task.context:
        parts.append(f"## Context\n{task.context}")

    # 3. Predecessor results (only from depends_on tasks)
    if predecessor_results and task.depends_on:
        predecessor_parts = []
        for dep_id in task.depends_on:
            dep_result = predecessor_results.get(dep_id)
            if dep_result and dep_result.content:
                predecessor_parts.append(f"### Results from {dep_id}\n{dep_result.content}")
        if predecessor_parts:
            parts.append("## Prior Results\n" + "\n\n".join(predecessor_parts))

    return "\n\n".join(parts)
