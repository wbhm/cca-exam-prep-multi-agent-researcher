"""Hub-and-spoke coordinator — the centerpiece of the architecture.

The coordinator follows a 6-step flow:
1. PLAN    — Decompose query into SubTasks (can use LLM or pre-built scenarios)
2. SORT    — Topological sort by depends_on into parallel waves
3. DELEGATE — For each wave: build_subagent_context -> run_agent_loop
4. EVALUATE — Send results to fact_checker for cross-referencing
5. RESOLVE  — conflict_resolver produces ConflictRecords
6. SYNTHESIZE — Compile final ResearchReport

CCA Key Concept: The coordinator is the hub. Subagents (spokes) only talk
to the coordinator, never to each other. All coordination is centralized.
"""

from __future__ import annotations

from research_agents.agent.agent_loop import AgentResult, run_agent_loop
from research_agents.agent.conflict_resolver import resolve_conflicts
from research_agents.agent.context_builder import build_subagent_context
from research_agents.agent.subagents import SUBAGENT_CONFIGS
from research_agents.models.research import (
    ResearchReport,
    SourceReliability,
    SourceResult,
    SubTask,
)
from research_agents.services.container import ServiceContainer


def sort_tasks_into_waves(tasks: list[SubTask]) -> list[list[SubTask]]:
    """Topological sort of tasks into parallel execution waves.

    Tasks with no depends_on go in wave 0. Tasks depending on wave-0
    results go in wave 1, etc.
    """
    completed: set[str] = set()
    remaining = list(tasks)
    waves: list[list[SubTask]] = []

    while remaining:
        wave = [t for t in remaining if all(d in completed for d in t.depends_on)]
        if not wave:
            # Circular dependency or unresolvable — put everything in one wave
            wave = remaining
            remaining = []
        else:
            remaining = [t for t in remaining if t not in wave]
        waves.append(wave)
        completed.update(t.task_id for t in wave)

    return waves


def run_coordinator(
    client: object,
    services: ServiceContainer,
    tasks: list[SubTask],
    model: str = "claude-sonnet-4-6",
) -> tuple[dict[str, AgentResult], list[list[SubTask]]]:
    """Execute the delegation phase of the coordinator.

    Steps 2-3 of the 6-step flow: sort into waves, then delegate each task.

    Args:
        client: Anthropic client (or mock)
        services: ServiceContainer
        tasks: Pre-decomposed SubTasks (step 1 is done by caller)
        model: Claude model ID

    Returns:
        Tuple of (results dict keyed by task_id, waves list)
    """
    waves = sort_tasks_into_waves(tasks)
    results: dict[str, AgentResult] = {}

    for wave in waves:
        for task in wave:
            config = SUBAGENT_CONFIGS.get(task.agent_type)
            if config is None:
                results[task.task_id] = AgentResult(
                    content=f"Error: unknown agent_type '{task.agent_type}'"
                )
                continue

            # Build explicit context (context isolation enforced here)
            context_string = build_subagent_context(task, predecessor_results=results)

            # Run the subagent with scoped tools
            result = run_agent_loop(
                client=client,
                services=services,
                user_message=context_string,
                system_prompt=config.system_prompt,
                tools=config.tools,
                agent_type=task.agent_type,
                model=model,
            )
            results[task.task_id] = result

    return results, waves


def build_research_report(
    query: str,
    results: dict[str, AgentResult],
    reliability_lookup: dict[str, SourceReliability],
    conflicts: list[dict] | None = None,
    gaps: list[str] | None = None,
) -> ResearchReport:
    """Steps 5-6 of the coordinator flow: resolve conflicts and compile report.

    Args:
        query: The original research query
        results: Subagent results keyed by task_id
        reliability_lookup: URL -> SourceReliability mapping
        conflicts: List of detected conflicts (claim, sources_for, sources_against)
        gaps: List of sources that were unavailable

    Returns:
        Final ResearchReport.
    """
    # Resolve conflicts
    conflict_records = []
    if conflicts:
        conflict_records = resolve_conflicts(conflicts, reliability_lookup)

    # Build findings from results
    findings: list[SourceResult] = []
    synthesis_parts: list[str] = []
    for task_id, result in results.items():
        if result.content:
            synthesis_parts.append(result.content)
            findings.append(
                SourceResult(
                    source_url=f"agent:{task_id}",
                    title=f"Results from {task_id}",
                    content_summary=result.content[:500],
                    reliability=SourceReliability.HIGH,
                )
            )

    # Calculate confidence
    base_confidence = 0.8
    if gaps:
        base_confidence -= 0.1 * len(gaps)
    if conflict_records:
        flagged = [c for c in conflict_records if c.resolution == "flagged_for_human"]
        base_confidence -= 0.05 * len(flagged)
    confidence = max(0.1, min(1.0, base_confidence))

    return ResearchReport(
        query=query,
        findings=findings,
        conflicts=conflict_records,
        synthesis="\n\n".join(synthesis_parts),
        confidence_score=confidence,
        gaps=gaps or [],
    )
