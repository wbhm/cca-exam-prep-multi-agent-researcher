"""Tests for simulated services."""

from __future__ import annotations

import pytest

from research_agents.models.research import SourceReliability
from research_agents.services.container import ServiceContainer
from research_agents.services.database import DatabaseService, TableNotFoundError
from research_agents.services.document_store import DocumentNotFoundError, DocumentStore
from research_agents.services.knowledge_base import KnowledgeBase
from research_agents.services.web_search import (
    WebSearchNotFoundError,
    WebSearchService,
    WebSearchTimeoutError,
)


# --- WebSearchService ---

class TestWebSearchService:
    def test_search_returns_results(self, services: ServiceContainer):
        results = services.web_search.search("renewable energy")
        assert len(results) >= 2
        assert all(r.url for r in results)

    def test_search_no_match(self, services: ServiceContainer):
        results = services.web_search.search("quantum teleportation xyz")
        assert results == []

    def test_fetch_page_success(self, services: ServiceContainer):
        page = services.web_search.fetch_page("https://energy.gov/renewable-2024")
        assert "30%" in page.text
        assert page.reliability == SourceReliability.HIGH

    def test_fetch_page_timeout(self, services: ServiceContainer):
        with pytest.raises(WebSearchTimeoutError, match="Timeout"):
            services.web_search.fetch_page("https://timeout.example.com/remote-data")

    def test_fetch_page_not_found(self, services: ServiceContainer):
        with pytest.raises(WebSearchNotFoundError, match="404"):
            services.web_search.fetch_page("https://healthtech.example.com/ai-revolution")

    def test_fetch_page_unknown_url(self, services: ServiceContainer):
        with pytest.raises(WebSearchNotFoundError):
            services.web_search.fetch_page("https://totally-unknown.example.com")

    def test_available_keywords(self, services: ServiceContainer):
        keywords = services.web_search.available_keywords
        assert "renewable energy" in keywords


# --- DocumentStore ---

class TestDocumentStore:
    def test_get_document(self, services: ServiceContainer):
        doc = services.document_store.get_document("doc-renewable-iea")
        assert doc.title == "IEA World Energy Outlook 2024"
        assert len(doc.sections) >= 2

    def test_get_document_not_found(self, services: ServiceContainer):
        with pytest.raises(DocumentNotFoundError):
            services.document_store.get_document("nonexistent")

    def test_list_documents(self, services: ServiceContainer):
        docs = services.document_store.list_documents()
        assert len(docs) >= 3

    def test_search_by_title(self, services: ServiceContainer):
        results = services.document_store.search_by_title("AI")
        assert len(results) >= 1
        assert "AI" in results[0].title

    def test_document_ids(self, services: ServiceContainer):
        assert "doc-renewable-iea" in services.document_store.document_ids


# --- DatabaseService ---

class TestDatabaseService:
    def test_query_all_rows(self, services: ServiceContainer):
        rows = services.database.query("renewable_capacity")
        assert len(rows) >= 4

    def test_query_with_filter(self, services: ServiceContainer):
        rows = services.database.query("renewable_capacity", filters={"source": "solar"})
        assert all(r["source"] == "solar" for r in rows)
        assert len(rows) >= 2

    def test_query_table_not_found(self, services: ServiceContainer):
        with pytest.raises(TableNotFoundError):
            services.database.query("nonexistent_table")

    def test_get_schema(self, services: ServiceContainer):
        schema = services.database.get_schema("renewable_capacity")
        assert schema["table"] == "renewable_capacity"
        col_names = [c["name"] for c in schema["columns"]]
        assert "year" in col_names
        assert "capacity_gw" in col_names

    def test_table_names(self, services: ServiceContainer):
        names = services.database.table_names
        assert "renewable_capacity" in names
        assert "remote_work_stats" in names


# --- KnowledgeBase ---

class TestKnowledgeBase:
    def test_lookup_fact_found(self, services: ServiceContainer):
        facts = services.knowledge_base.lookup_fact("renewable energy 30%")
        assert len(facts) >= 1
        verified = [f for f in facts if f.verified]
        assert len(verified) >= 1

    def test_lookup_fact_ranks_closest_claim_first(self, services: ServiceContainer):
        """The debunked 45% record must outrank the verified 30% record for a 45% claim."""
        facts = services.knowledge_base.lookup_fact(
            "Renewable energy accounts for 45% of global electricity"
        )
        assert len(facts) >= 2
        assert facts[0].verified is False
        assert facts[0].confidence == 0.10

    def test_lookup_fact_not_found(self, services: ServiceContainer):
        facts = services.knowledge_base.lookup_fact("quantum teleportation xyz")
        assert facts == []

    def test_source_reliability_exact(self, services: ServiceContainer):
        r = services.knowledge_base.get_source_reliability("energy.gov")
        assert r == SourceReliability.HIGH

    def test_source_reliability_domain_match(self, services: ServiceContainer):
        r = services.knowledge_base.get_source_reliability("https://energy.gov/some-page")
        assert r == SourceReliability.HIGH

    def test_source_reliability_unknown(self, services: ServiceContainer):
        r = services.knowledge_base.get_source_reliability("https://random-site.xyz")
        assert r == SourceReliability.UNKNOWN

    def test_fact_count(self, services: ServiceContainer):
        assert services.knowledge_base.fact_count >= 4


# --- ServiceContainer ---

class TestServiceContainer:
    def test_is_frozen(self, services: ServiceContainer):
        with pytest.raises(AttributeError):
            services.web_search = None  # type: ignore[misc]

    def test_all_services_present(self, services: ServiceContainer):
        assert services.web_search is not None
        assert services.document_store is not None
        assert services.database is not None
        assert services.knowledge_base is not None
