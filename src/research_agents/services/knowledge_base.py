"""Simulated knowledge base for fact-checking.

Contains verified facts with confidence scores and source reliability.
Used by the fact_checker subagent to verify claims from other subagents.
"""

from __future__ import annotations

from research_agents.models.research import FactRecord, SourceReliability
from research_agents.services.reliability import match_reliability


def _words(text: str) -> list[str]:
    """Lower-cased tokens of three or more characters ("30%" counts; "of" does not)."""
    return [w for w in text.lower().split() if len(w) >= 3]


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
        """Find facts related to a claim, closest match first.

        Each stored fact is scored by how many of its words (3+ chars) appear
        in the claim. Matches are returned by descending overlap, then by
        descending confidence. Ranking by overlap matters: the verified
        "30% renewable" record and the debunked "45% renewable" record share
        most words, and a caller that simply picked the highest-confidence
        match would certify the debunked claim as true.
        """
        claim_words = set(_words(claim))
        scored = []
        for fact in self._facts:
            overlap = sum(1 for word in _words(fact.claim) if word in claim_words)
            if overlap:
                scored.append((overlap, fact.confidence, fact))
        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [fact for _, _, fact in scored]

    def get_source_reliability(self, url: str) -> SourceReliability:
        """Look up the reliability rating for a source URL (exact, then domain match)."""
        return match_reliability(url, self._source_reliability)

    @property
    def fact_count(self) -> int:
        return len(self._facts)

    @property
    def known_sources(self) -> list[str]:
        return list(self._source_reliability.keys())
