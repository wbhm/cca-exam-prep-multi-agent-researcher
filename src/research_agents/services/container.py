"""Service container bundling all simulated services.

Follows the same frozen-dataclass pattern as the sibling customer_service project.
Services are injected into tool handlers, never imported directly.
"""

from __future__ import annotations

from dataclasses import dataclass

from research_agents.services.database import DatabaseService
from research_agents.services.document_store import DocumentStore
from research_agents.services.knowledge_base import KnowledgeBase
from research_agents.services.web_search import WebSearchService


@dataclass(frozen=True)
class ServiceContainer:
    """Immutable container holding all simulated research services."""

    web_search: WebSearchService
    document_store: DocumentStore
    database: DatabaseService
    knowledge_base: KnowledgeBase


def make_default_services() -> ServiceContainer:
    """Fresh container over the deterministic seed data in ``data/sources``.

    Used by the notebooks and by the test fixture. The container is new each
    time; the seed collections themselves are shared module-level objects.
    """
    from research_agents.data.sources import (
        DATABASE_TABLES,
        DOCUMENTS,
        NOT_FOUND_URLS,
        PAGE_CONTENT,
        SEARCH_INDEX,
        SOURCE_RELIABILITY_RATINGS,
        TIMEOUT_URLS,
        VERIFIED_FACTS,
    )

    return ServiceContainer(
        web_search=WebSearchService(
            search_index=SEARCH_INDEX,
            pages=PAGE_CONTENT,
            timeout_urls=TIMEOUT_URLS,
            not_found_urls=NOT_FOUND_URLS,
        ),
        document_store=DocumentStore(documents=DOCUMENTS),
        database=DatabaseService(tables=DATABASE_TABLES),
        knowledge_base=KnowledgeBase(
            facts=VERIFIED_FACTS,
            source_reliability=SOURCE_RELIABILITY_RATINGS,
        ),
    )
