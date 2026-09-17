"""Hub-and-spoke coordinator — the centerpiece of the architecture.

The coordinator follows a 6-step flow:
1. PLAN    — Decompose query into SubTasks. Done by the caller (notebooks
             hand-write the SubTask list); this module has no decomposition code.
2. SORT    — Topological sort by depends_on into parallel waves
3. DELEGATE — For each wave: build_subagent_context -> run_agent_loop
4. EVALUATE — A fact_checker SubTask that depends_on the others; its
             flag_conflict results are the conflicts fed to step 5.
5. RESOLVE  — conflict_resolver produces ConflictRecords
6. SYNTHESIZE — Compile final ResearchReport; gaps are collected
             programmatically from structured tool errors (collect_gaps).

CCA Key Concept: The coordinator is the hub. Subagents (spokes) only talk
to the coordinator, never to each other. All coordination is centralized.
"""

from __future__ import annotations

import json

from research_agents.agent.agent_loop import AgentResult, DispatchFn, run_agent_loop
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
from research_agents.tools.handlers import dispatch


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
    max_iterations: int = 10,
    dispatch_fn: DispatchFn = dispatch,
) -> tuple[dict[str, AgentResult], list[list[SubTask]]]:
    """Execute the delegation phase of the coordinator.

    Steps 2-3 of the 6-step flow: sort into waves, then delegate each task.
    Tasks inside a wave are independent but are executed one after another;
    "parallel" describes the dependency structure, not concurrency.

    Args:
        client: Anthropic client (or mock)
        services: ServiceContainer
        tasks: Pre-decomposed SubTasks (step 1 is done by caller)
        model: Claude model ID
        max_iterations: Per-subagent loop limit
        dispatch_fn: Tool router passed to every subagent loop

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
                max_iterations=max_iterations,
                dispatch_fn=dispatch_fn,
            )
            results[task.task_id] = result

    return results, waves


def collect_tool_errors(results: dict[str, AgentResult]) -> list[dict]:
    """Every structured tool error any subagent received, in call order.

    Reads ``AgentResult.tool_results`` (the loop's log), never the model's
    prose, so a subagent that "forgot" to mention a timeout cannot hide it.
    """
    errors: list[dict] = []
    for task_id, result in results.items():
        for entry in result.tool_results:
            try:
                payload = json.loads(entry["result"])
            except (ValueError, TypeError):
                continue
            if payload.get("status") != "error":
                continue
            errors.append({
                "task_id": task_id,
                "tool_name": entry["tool_name"],
                "error_type": payload.get("error_type", "unknown"),
                "source": payload.get("source", ""),
                "retry_eligible": bool(payload.get("retry_eligible", False)),
                "fallback_available": bool(payload.get("fallback_available", False)),
            })
    return errors


def collect_gaps(results: dict[str, AgentResult]) -> list[str]:
    """Gap strings for the report: one per tool error, plus any cut-off subagent."""
    gaps = [f"{e['source']} ({e['error_type']})" for e in collect_tool_errors(results)]
    gaps.extend(
        f"{task_id} (max_iterations)"
        for task_id, result in results.items()
        if result.stop_reason == "max_iterations"
    )
    return gaps


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
        gaps: Sources that were unavailable. When omitted, derived from the
            subagents' structured tool errors via ``collect_gaps``.

    Returns:
        Final ResearchReport. Findings are one entry per subagent transcript
        (``source_url="agent:<task_id>"``), not per underlying source.
    """
    if gaps is None:
        gaps = collect_gaps(results)

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
    confidence = round(max(0.1, min(1.0, base_confidence)), 2)

    return ResearchReport(
        query=query,
        findings=findings,
        conflicts=conflict_records,
        synthesis="\n\n".join(synthesis_parts),
        confidence_score=confidence,
        gaps=gaps,
    )
