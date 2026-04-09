"""Simulated web search service with pre-built results.

Some URLs intentionally return errors (timeouts, 404s) to demonstrate
structured error handling vs. silent failures.
"""

from __future__ import annotations

from research_agents.models.research import PageContent, SearchResult


class WebSearchTimeoutError(Exception):
    """Raised when a simulated fetch times out."""


class WebSearchNotFoundError(Exception):
    """Raised when a simulated URL returns 404."""


class WebSearchService:
    """In-memory web search with pre-built results indexed by keyword."""

    def __init__(
        self,
        search_index: dict[str, list[SearchResult]],
        pages: dict[str, PageContent],
        timeout_urls: set[str] | None = None,
        not_found_urls: set[str] | None = None,
    ) -> None:
        self._search_index = search_index
        self._pages = pages
        self._timeout_urls = timeout_urls or set()
        self._not_found_urls = not_found_urls or set()

    def search(self, query: str) -> list[SearchResult]:
        """Search for results matching any keyword in the query."""
        query_lower = query.lower()
        results: list[SearchResult] = []
        seen_urls: set[str] = set()
        for keyword, hits in self._search_index.items():
            if keyword.lower() in query_lower:
                for hit in hits:
                    if hit.url not in seen_urls:
                        results.append(hit)
                        seen_urls.add(hit.url)
        return results

    def fetch_page(self, url: str) -> PageContent:
        """Fetch a page by URL. May raise timeout or not-found errors."""
        if url in self._timeout_urls:
            raise WebSearchTimeoutError(f"Timeout fetching {url}")
        if url in self._not_found_urls:
            raise WebSearchNotFoundError(f"404 Not Found: {url}")
        if url not in self._pages:
            raise WebSearchNotFoundError(f"No page data for {url}")
        return self._pages[url]

    @property
    def available_keywords(self) -> list[str]:
        return list(self._search_index.keys())
