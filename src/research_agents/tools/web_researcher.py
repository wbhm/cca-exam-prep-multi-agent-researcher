"""Tool handlers for the Web Researcher agent.

Every handler returns a JSON string — structured errors on failure.
"""

from __future__ import annotations

import json

from research_agents.services.container import ServiceContainer
from research_agents.services.web_search import WebSearchNotFoundError, WebSearchTimeoutError
from research_agents.tools._errors import error_response


def handle_search_web(input_dict: dict, services: ServiceContainer) -> str:
    query = input_dict.get("query", "")
    if not query:
        return error_response(
            "invalid_input",
            "search_web",
            "Query parameter is required",
        )
    results = services.web_search.search(query)
    return json.dumps({
        "status": "success",
        "data": [r.model_dump() for r in results],
    })


def handle_fetch_page(input_dict: dict, services: ServiceContainer) -> str:
    url = input_dict.get("url", "")
    if not url:
        return error_response(
            "invalid_input",
            "fetch_page",
            "URL parameter is required",
        )
    try:
        page = services.web_search.fetch_page(url)
        return json.dumps({
            "status": "success",
            "data": page.model_dump(),
        })
    except WebSearchTimeoutError:
        return error_response(
            "timeout",
            url,
            f"Timeout fetching {url}",
            retry_eligible=True,
        )
    except WebSearchNotFoundError:
        return error_response(
            "not_found",
            url,
            f"Page not found: {url}",
            fallback_available=True,
        )


def handle_extract_text(input_dict: dict, services: ServiceContainer) -> str:
    url = input_dict.get("url", "")
    if not url:
        return error_response(
            "invalid_input",
            "extract_text",
            "URL parameter is required",
        )
    try:
        page = services.web_search.fetch_page(url)
        return json.dumps({
            "status": "success",
            "data": {"url": page.url, "title": page.title, "text": page.text},
        })
    except (WebSearchTimeoutError, WebSearchNotFoundError) as e:
        error_type = "timeout" if isinstance(e, WebSearchTimeoutError) else "not_found"
        return error_response(
            error_type,
            url,
            str(e),
            retry_eligible=isinstance(e, WebSearchTimeoutError),
        )


def handle_summarize_source(input_dict: dict, services: ServiceContainer) -> str:
    url = input_dict.get("url", "")
    if not url:
        return error_response(
            "invalid_input",
            "summarize_source",
            "URL parameter is required",
        )
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
        return error_response(
            error_type,
            url,
            str(e),
            retry_eligible=isinstance(e, WebSearchTimeoutError),
        )
