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
        """Strategy 2: When the best tier on each side is equal, majority count wins."""
        record = resolve_conflict(
            claim="Remote work boosts productivity",
            sources_for=["https://reuters.com", "https://news.example.com", "https://ap.example.com"],
            sources_against=["https://blog.example.com"],
            reliability_lookup={
                "https://reuters.com": SourceReliability.MEDIUM,
                "https://news.example.com": SourceReliability.MEDIUM,
                "https://ap.example.com": SourceReliability.MEDIUM,
                "https://blog.example.com": SourceReliability.MEDIUM,
            },
        )
        # All MEDIUM → tiers tie → 3 of 4 agree → majority, confidence 0.75
        assert record.resolution == "majority"
        assert record.confidence == 0.75
        assert record.winning_side == "for"

    def test_majority_can_favour_against(self):
        """2 HIGH for vs 3 HIGH against → majority, against wins, 3/5 = 0.6."""
        lookup = {f"https://s{i}.gov": SourceReliability.HIGH for i in range(5)}
        record = resolve_conflict(
            claim="Claim",
            sources_for=["https://s0.gov", "https://s1.gov"],
            sources_against=["https://s2.gov", "https://s3.gov", "https://s4.gov"],
            reliability_lookup=lookup,
        )
        assert record.resolution == "majority"
        assert record.confidence == 0.6
        assert record.winning_side == "against"

    def test_many_low_sources_do_not_outrank_one_high(self):
        """Tier comparison: three blogs never tie a single .gov source."""
        record = resolve_conflict(
            claim="Claim",
            sources_for=["https://b1.example.com", "https://b2.example.com", "https://b3.example.com"],
            sources_against=["https://energy.gov"],
            reliability_lookup={
                "https://b1.example.com": SourceReliability.LOW,
                "https://b2.example.com": SourceReliability.LOW,
                "https://b3.example.com": SourceReliability.LOW,
                "https://energy.gov": SourceReliability.HIGH,
            },
        )
        assert record.resolution == "highest_reliability"
        assert record.winning_side == "against"
        assert record.confidence == 0.8  # tier gap 2 → 0.5 + 2 * 0.15

    def test_domain_keyed_lookup_matches_full_urls(self):
        """Reliability data keyed by domain must apply to full source URLs."""
        record = resolve_conflict(
            claim="Renewable energy is 30%",
            sources_for=["https://energy.gov/renewable-2024"],
            sources_against=["https://energyblog.example.com/renewables"],
            reliability_lookup={
                "energy.gov": SourceReliability.HIGH,
                "energyblog.example.com": SourceReliability.LOW,
            },
        )
        assert record.resolution == "highest_reliability"
        assert record.winning_side == "for"

    def test_swapping_sides_flips_winner_only(self):
        """Deterministic: the same evidence yields the same verdict regardless of list order."""
        lookup = {
            "https://energy.gov": SourceReliability.HIGH,
            "https://blog.example.com": SourceReliability.LOW,
        }
        a = resolve_conflict("c", ["https://energy.gov"], ["https://blog.example.com"], lookup)
        b = resolve_conflict("c", ["https://blog.example.com"], ["https://energy.gov"], lookup)
        assert (a.resolution, a.confidence) == (b.resolution, b.confidence)
        assert a.winning_side == "for"
        assert b.winning_side == "against"

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
        assert record.winning_side == "undecided"

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

    def test_missing_claim_key_does_not_raise(self):
        records = resolve_conflicts([{"sources_for": ["https://energy.gov"]}], RELIABILITY)
        assert len(records) == 1
        assert records[0].claim == ""

    def test_empty_conflicts(self):
        records = resolve_conflicts([], RELIABILITY)
        assert records == []
