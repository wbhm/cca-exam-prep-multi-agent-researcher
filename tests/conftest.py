"""Shared test fixtures.

Creates a fresh ServiceContainer with seed data for every test.
No actual API calls are made — all services are simulated in-memory.
"""

from __future__ import annotations

import pytest

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
from research_agents.services.container import ServiceContainer
from research_agents.services.database import DatabaseService
from research_agents.services.document_store import DocumentStore
from research_agents.services.knowledge_base import KnowledgeBase
from research_agents.services.web_search import WebSearchService


@pytest.fixture
def services() -> ServiceContainer:
    """Create a fresh ServiceContainer with all seed data."""
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


def make_services() -> ServiceContainer:
    """Functional helper used in notebooks (no pytest fixture needed)."""
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
