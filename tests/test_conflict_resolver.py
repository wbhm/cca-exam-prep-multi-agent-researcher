"""Tests for deterministic conflict resolution."""

from __future__ import annotations

from research_agents.agent.conflict_resolver import resolve_conflict, resolve_conflicts
from research_agents.models.research import SourceReliability


RELIABILITY: dict[str, SourceReliability] = {
    "https://energy.gov": SourceReliability.HIGH,
    "https://reuters.com": SourceReliability.MEDIUM,
    "https://blog.example.com": SourceReliability.LOW,
    "https://nature.com": SourceReliability.HIGH,
    "https://news.example.com": SourceReliability.MEDIUM,
}


class TestResolveConflict:
    def test_highest_reliability_wins(self):
        """Strategy 1: High-reliability source beats low-reliability."""
        record = resolve_conflict(
            claim="Renewable energy is 30%",
            sources_for=["https://energy.gov"],
            sources_against=["https://blog.example.com"],
            reliability_lookup=RELIABILITY,
        )
        assert record.resolution == "highest_reliability"
        assert record.confidence > 0.5

    def test_majority_consensus(self):
        """Strategy 2: When reliability is tied, majority wins."""
        record = resolve_conflict(
            claim="Remote work boosts productivity",
            sources_for=["https://reuters.com", "https://news.example.com"],
            sources_against=["https://blog.example.com"],
            reliability_lookup={
                "https://reuters.com": SourceReliability.MEDIUM,
                "https://news.example.com": SourceReliability.LOW,
                "https://blog.example.com": SourceReliability.LOW,
            },
        )
        # reuters(2) + news(1) = 3 vs blog(1) = 1 → reliability wins
        assert record.resolution == "highest_reliability"

    def test_true_majority_when_scores_equal(self):
        """When reliability scores are exactly equal, majority count wins."""
        record = resolve_conflict(
            claim="Some claim",
            sources_for=["https://a.com", "https://b.com"],
            sources_against=["https://c.com"],
            reliability_lookup={
                "https://a.com": SourceReliability.LOW,
                "https://b.com": SourceReliability.UNKNOWN,
                "https://c.com": SourceReliability.LOW,
            },
        )
        # a(1) + b(0) = 1 vs c(1) = 1 → tied scores → majority (2 vs 1)
        assert record.resolution == "majority"

    def test_flagged_for_human(self):
        """Strategy 3: Equal reliability AND equal count → human review."""
        record = resolve_conflict(
            claim="Disputed claim",
            sources_for=["https://reuters.com"],
            sources_against=["https://news.example.com"],
            reliability_lookup=RELIABILITY,
        )
        # Both MEDIUM (score 2 each), both 1 source → flagged
        assert record.resolution == "flagged_for_human"
        assert record.confidence <= 0.5

    def test_confidence_increases_with_score_gap(self):
        """Larger reliability gap → higher confidence."""
        record = resolve_conflict(
            claim="Strong consensus",
            sources_for=["https://energy.gov", "https://nature.com"],
            sources_against=["https://blog.example.com"],
            reliability_lookup=RELIABILITY,
        )
        assert record.confidence > 0.7


class TestResolveConflicts:
    def test_batch_resolution(self):
        conflicts = [
            {
                "claim": "Claim A",
                "sources_for": ["https://energy.gov"],
                "sources_against": ["https://blog.example.com"],
            },
            {
                "claim": "Claim B",
                "sources_for": ["https://reuters.com"],
                "sources_against": ["https://news.example.com"],
            },
        ]
        records = resolve_conflicts(conflicts, RELIABILITY)
        assert len(records) == 2
        assert records[0].resolution == "highest_reliability"
        assert records[1].resolution == "flagged_for_human"

    def test_empty_conflicts(self):
        records = resolve_conflicts([], RELIABILITY)
        assert records == []
