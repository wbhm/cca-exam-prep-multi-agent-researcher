"""Tool handlers for the Web Researcher agent.

Every handler returns a JSON string — structured errors on failure.
"""

from __future__ import annotations

import json

from research_agents.services.container import ServiceContainer
from research_agents.services.web_search import WebSearchNotFoundError, WebSearchTimeoutError


def handle_search_web(input_dict: dict, services: ServiceContainer) -> str:
    query = input_dict.get("query", "")
    if not query:
        return json.dumps({
            "status": "error",
            "error_type": "invalid_input",
            "source": "search_web",
            "message": "Query parameter is required",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })
    results = services.web_search.search(query)
    return json.dumps({
        "status": "success",
        "data": [r.model_dump() for r in results],
    })


def handle_fetch_page(input_dict: dict, services: ServiceContainer) -> str:
    url = input_dict.get("url", "")
    if not url:
        return json.dumps({
            "status": "error",
            "error_type": "invalid_input",
            "source": "fetch_page",
            "message": "URL parameter is required",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })
    try:
        page = services.web_search.fetch_page(url)
        return json.dumps({
            "status": "success",
            "data": page.model_dump(),
        })
    except WebSearchTimeoutError:
        return json.dumps({
            "status": "error",
            "error_type": "timeout",
            "source": url,
            "message": f"Timeout fetching {url}",
            "retry_eligible": True,
            "fallback_available": False,
            "partial_data": None,
        })
    except WebSearchNotFoundError:
        return json.dumps({
            "status": "error",
            "error_type": "not_found",
            "source": url,
            "message": f"Page not found: {url}",
            "retry_eligible": False,
            "fallback_available": True,
            "partial_data": None,
        })


def handle_extract_text(input_dict: dict, services: ServiceContainer) -> str:
    url = input_dict.get("url", "")
    if not url:
        return json.dumps({
            "status": "error",
            "error_type": "invalid_input",
            "source": "extract_text",
            "message": "URL parameter is required",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })
    try:
        page = services.web_search.fetch_page(url)
        return json.dumps({
            "status": "success",
            "data": {"url": page.url, "title": page.title, "text": page.text},
        })
    except (WebSearchTimeoutError, WebSearchNotFoundError) as e:
        error_type = "timeout" if isinstance(e, WebSearchTimeoutError) else "not_found"
        return json.dumps({
            "status": "error",
            "error_type": error_type,
            "source": url,
            "message": str(e),
            "retry_eligible": isinstance(e, WebSearchTimeoutError),
            "fallback_available": False,
            "partial_data": None,
        })


def handle_summarize_source(input_dict: dict, services: ServiceContainer) -> str:
    url = input_dict.get("url", "")
    if not url:
        return json.dumps({
            "status": "error",
            "error_type": "invalid_input",
            "source": "summarize_source",
            "message": "URL parameter is required",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })
    try:
        page = services.web_search.fetch_page(url)
        reliability = services.knowledge_base.get_source_reliability(url)
        return json.dumps({
            "status": "success",
            "data": {
                "url": page.url,
                "title": page.title,
                "summary": page.text[:200] + "..." if len(page.text) > 200 else page.text,
                "reliability": reliability.value,
            },
        })
    except (WebSearchTimeoutError, WebSearchNotFoundError) as e:
        error_type = "timeout" if isinstance(e, WebSearchTimeoutError) else "not_found"
        return json.dumps({
            "status": "error",
            "error_type": error_type,
            "source": url,
            "message": str(e),
            "retry_eligible": isinstance(e, WebSearchTimeoutError),
            "fallback_available": False,
            "partial_data": None,
        })
