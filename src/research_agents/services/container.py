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
