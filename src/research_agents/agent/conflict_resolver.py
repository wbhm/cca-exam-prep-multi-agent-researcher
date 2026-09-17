"""Deterministic conflict resolution.

CCA Key Concept: Conflicts are resolved using programmatic rules, not LLM
judgment. Three strategies in priority order:
1. Source reliability ranking: the side whose *best* source sits in a higher
   tier wins (.gov > peer-reviewed > news > blog). Three blogs never outrank
   one government source.
2. Majority consensus: when both sides' best tier is equal, the side with
   more sources wins (3 of 4 agree → majority).
3. Flag for human review: equal tier and equal count.

Every record says which side won (``winning_side``) so the synthesis step can
state the verdict, not just the strategy used.
"""

from __future__ import annotations

from research_agents.models.research import ConflictRecord, SourceReliability
from research_agents.services.reliability import match_reliability

# Reliability scoring: higher = more trustworthy
RELIABILITY_SCORES: dict[SourceReliability, int] = {
    SourceReliability.HIGH: 3,
    SourceReliability.MEDIUM: 2,
    SourceReliability.LOW: 1,
    SourceReliability.UNKNOWN: 0,
}


def _best_tier(
    sources: list[str],
    reliability_lookup: dict[str, SourceReliability],
) -> int:
    """Score of the most reliable source in the group (0 if empty or all unknown).

    Ratings may be keyed by domain ("energy.gov") while sources are full URLs;
    ``match_reliability`` applies the same rule the knowledge base uses.
    """
    return max(
        (RELIABILITY_SCORES[match_reliability(src, reliability_lookup)] for src in sources),
        default=0,
    )


def resolve_conflict(
    claim: str,
    sources_for: list[str],
    sources_against: list[str],
    reliability_lookup: dict[str, SourceReliability],
) -> ConflictRecord:
    """Resolve a single conflict using the three-tier strategy.

    Args:
        claim: The disputed factual claim
        sources_for: URLs of sources supporting the claim
        sources_against: URLs of sources contradicting the claim
        reliability_lookup: Map of URL or domain -> SourceReliability

    Returns:
        ConflictRecord with resolution strategy, confidence, and winning side.
        The result depends only on the evidence, never on list order.
    """
    for_tier = _best_tier(sources_for, reliability_lookup)
    against_tier = _best_tier(sources_against, reliability_lookup)

    # Strategy 1: Source reliability ranking (best tier per side)
    if for_tier != against_tier:
        gap = abs(for_tier - against_tier)
        return ConflictRecord(
            claim=claim,
            sources_for=sources_for,
            sources_against=sources_against,
            resolution="highest_reliability",
            confidence=min(0.95, 0.5 + gap * 0.15),
            winning_side="for" if for_tier > against_tier else "against",
        )

    # Strategy 2: Majority consensus (tiers tie, counts differ)
    if len(sources_for) != len(sources_against):
        total = len(sources_for) + len(sources_against)
        majority_size = max(len(sources_for), len(sources_against))
        return ConflictRecord(
            claim=claim,
            sources_for=sources_for,
            sources_against=sources_against,
            resolution="majority",
            confidence=min(0.85, majority_size / total),
            winning_side="for" if len(sources_for) > len(sources_against) else "against",
        )

    # Strategy 3: Flag for human review (tiers tie, counts tie)
    return ConflictRecord(
        claim=claim,
        sources_for=sources_for,
        sources_against=sources_against,
        resolution="flagged_for_human",
        confidence=0.3,
        winning_side="undecided",
    )


def resolve_conflicts(
    conflicts: list[dict],
    reliability_lookup: dict[str, SourceReliability],
) -> list[ConflictRecord]:
    """Resolve all conflicts in a batch.

    Args:
        conflicts: List of dicts with keys: claim, sources_for, sources_against
        reliability_lookup: Map of URL or domain -> SourceReliability

    Returns:
        List of ConflictRecords with resolutions. Never raises on a missing key.
    """
    return [
        resolve_conflict(
            claim=conflict.get("claim", ""),
            sources_for=conflict.get("sources_for", []),
            sources_against=conflict.get("sources_against", []),
            reliability_lookup=reliability_lookup,
        )
        for conflict in conflicts
    ]
