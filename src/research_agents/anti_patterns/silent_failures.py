"""Anti-pattern: Silent failures returning success with null data.

CCA Exam: The coordinator cannot distinguish between "no relevant data
found" and "the subagent failed to retrieve data." Silent failures
create systematic bias in the final report — it reflects only the
sources that happened to be available, not the full picture.

The correct pattern is structured error context (ToolErrorResponse)
with error_type, retry_eligible, and partial_data.
"""

from __future__ import annotations

import json

from research_agents.services.container import ServiceContainer
from research_agents.services.web_search import WebSearchNotFoundError, WebSearchTimeoutError
from research_agents.tools.handlers import Handler, dispatch


def handle_search_web_silent(input_dict: dict, services: ServiceContainer) -> str:
    """ANTI-PATTERN: Returns success even on failure."""
    try:
        results = services.web_search.search(input_dict.get("query", ""))
        return json.dumps({"status": "success", "data": [r.model_dump() for r in results]})
    except Exception:
        return json.dumps({"status": "success", "data": None})  # SILENT FAILURE


def handle_fetch_page_silent(input_dict: dict, services: ServiceContainer) -> str:
    """ANTI-PATTERN: Returns success with null on timeout/404."""
    try:
        page = services.web_search.fetch_page(input_dict.get("url", ""))
        return json.dumps({"status": "success", "data": page.model_dump()})
    except (WebSearchTimeoutError, WebSearchNotFoundError):
        return json.dumps({"status": "success", "data": None})  # SILENT FAILURE
    except Exception:
        return json.dumps({"status": "success", "data": None})  # SILENT FAILURE


# Silent failure dispatch — maps same tool names but with silent handlers
SILENT_DISPATCH: dict[str, dict[str, Handler]] = {
    "web_researcher": {
        "search_web": handle_search_web_silent,
        "fetch_page": handle_fetch_page_silent,
    },
}


def silent_dispatch(
    agent_type: str, tool_name: str, input_dict: dict, services: ServiceContainer
) -> str:
    """ANTI-PATTERN router: silent handlers where defined, real ones elsewhere.

    Same signature as ``tools.handlers.dispatch`` so it can be injected into
    ``run_agent_loop(dispatch_fn=...)``. That lets a notebook replay one
    scripted transcript through both routers and compare what reaches the
    coordinator.
    """
    handler = SILENT_DISPATCH.get(agent_type, {}).get(tool_name)
    if handler is not None:
        return handler(input_dict, services)
    return dispatch(agent_type, tool_name, input_dict, services)
