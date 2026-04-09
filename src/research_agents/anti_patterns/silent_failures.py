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
SILENT_DISPATCH: dict[str, dict[str, object]] = {
    "web_researcher": {
        "search_web": handle_search_web_silent,
        "fetch_page": handle_fetch_page_silent,
    },
}
