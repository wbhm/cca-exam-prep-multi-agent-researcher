"""Simulated knowledge base for fact-checking.

Contains verified facts with confidence scores and source reliability.
Used by the fact_checker subagent to verify claims from other subagents.
"""

from __future__ import annotations

from research_agents.models.research import FactRecord, SourceReliability


class KnowledgeBase:
    """In-memory fact-checking reference indexed by claim keywords."""

    def __init__(
        self,
        facts: list[FactRecord],
        source_reliability: dict[str, SourceReliability],
    ) -> None:
        self._facts = facts
        self._source_reliability = source_reliability

    def lookup_fact(self, claim: str) -> list[FactRecord]:
        """Find facts related to a claim by keyword matching."""
        claim_lower = claim.lower()
        return [
            fact
            for fact in self._facts
            if any(word in claim_lower for word in fact.claim.lower().split())
        ]

    def get_source_reliability(self, url: str) -> SourceReliability:
        """Look up the reliability rating for a source URL."""
        # Check exact match first
        if url in self._source_reliability:
            return self._source_reliability[url]
        # Check domain match
        for known_url, reliability in self._source_reliability.items():
            if known_url in url or url in known_url:
                return reliability
        return SourceReliability.UNKNOWN

    @property
    def fact_count(self) -> int:
        return len(self._facts)

    @property
    def known_sources(self) -> list[str]:
        return list(self._source_reliability.keys())
