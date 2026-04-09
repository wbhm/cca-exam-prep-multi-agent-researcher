"""Simulated document store with pre-built research papers and reports.

Some documents contain contradicting claims for conflict resolution demos.
"""

from __future__ import annotations

from research_agents.models.research import Document


class DocumentNotFoundError(Exception):
    """Raised when a document ID is not in the store."""


class DocumentStore:
    """In-memory document store indexed by doc_id."""

    def __init__(self, documents: dict[str, Document]) -> None:
        self._documents = documents

    def get_document(self, doc_id: str) -> Document:
        """Retrieve a document by ID."""
        if doc_id not in self._documents:
            raise DocumentNotFoundError(f"Document not found: {doc_id}")
        return self._documents[doc_id]

    def list_documents(self) -> list[Document]:
        """List all available documents."""
        return list(self._documents.values())

    def search_by_title(self, keyword: str) -> list[Document]:
        """Find documents whose title contains the keyword."""
        keyword_lower = keyword.lower()
        return [
            doc for doc in self._documents.values() if keyword_lower in doc.title.lower()
        ]

    @property
    def document_ids(self) -> list[str]:
        return list(self._documents.keys())
