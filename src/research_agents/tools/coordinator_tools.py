"""Tool handlers for the Coordinator agent.

These are used when the coordinator itself runs as an LLM-driven agent.
In the simpler orchestration mode, the coordinator calls subagents directly.
"""

from __future__ import annotations

import json

from research_agents.services.container import ServiceContainer


def handle_delegate_task(input_dict: dict, services: ServiceContainer) -> str:
    agent_type = input_dict.get("agent_type", "")
    instruction = input_dict.get("instruction", "")
    context = input_dict.get("context", "")
    if not all([agent_type, instruction]):
        return json.dumps({
            "status": "error",
            "error_type": "invalid_input",
            "source": "delegate_task",
            "message": "agent_type and instruction are required",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })
    valid_agents = {"web_researcher", "document_analyzer", "data_extractor", "fact_checker"}
    if agent_type not in valid_agents:
        return json.dumps({
            "status": "error",
            "error_type": "invalid_input",
            "source": "delegate_task",
            "message": f"Unknown agent_type: {agent_type}. Valid: {sorted(valid_agents)}",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })
    return json.dumps({
        "status": "success",
        "data": {
            "delegated": True,
            "agent_type": agent_type,
            "instruction": instruction,
            "context_length": len(context),
        },
    })


def handle_collect_results(input_dict: dict, services: ServiceContainer) -> str:
    task_ids = input_dict.get("task_ids", [])
    return json.dumps({
        "status": "success",
        "data": {"task_ids": task_ids, "collected": len(task_ids)},
    })


def handle_resolve_conflicts(input_dict: dict, services: ServiceContainer) -> str:
    conflicts = input_dict.get("conflicts", [])
    return json.dumps({
        "status": "success",
        "data": {"conflicts_received": len(conflicts), "resolved": len(conflicts)},
    })


def handle_compile_report(input_dict: dict, services: ServiceContainer) -> str:
    findings = input_dict.get("findings_summary", "")
    conflicts = input_dict.get("conflicts", [])
    gaps = input_dict.get("gaps", [])
    return json.dumps({
        "status": "success",
        "data": {
            "report_compiled": True,
            "findings_length": len(findings),
            "conflict_count": len(conflicts),
            "gap_count": len(gaps),
        },
    })
