"""Deterministic conflict resolution.

CCA Key Concept: Conflicts are resolved using programmatic rules, not LLM
judgment. Three strategies in priority order:
1. Source reliability ranking (.gov > peer-reviewed > news > blog)
2. Majority consensus (if 3 of 4 agree, majority wins)
3. Flag for human review (equal reliability, split sources)
"""

from __future__ import annotations

from research_agents.models.research import ConflictRecord, SourceReliability

# Reliability scoring: higher = more trustworthy
RELIABILITY_SCORES: dict[SourceReliability, int] = {
    SourceReliability.HIGH: 3,
    SourceReliability.MEDIUM: 2,
    SourceReliability.LOW: 1,
    SourceReliability.UNKNOWN: 0,
}


def _score_sources(
    sources: list[str],
    reliability_lookup: dict[str, SourceReliability],
) -> int:
    """Sum reliability scores for a group of sources."""
    return sum(
        RELIABILITY_SCORES.get(reliability_lookup.get(src, SourceReliability.UNKNOWN), 0)
        for src in sources
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
        reliability_lookup: Map of URL -> SourceReliability

    Returns:
        ConflictRecord with resolution strategy and confidence.
    """
    for_score = _score_sources(sources_for, reliability_lookup)
    against_score = _score_sources(sources_against, reliability_lookup)

    # Strategy 1: Source reliability ranking
    if for_score != against_score:
        if for_score > against_score:
            resolution = "highest_reliability"
            confidence = min(0.95, 0.5 + (for_score - against_score) * 0.15)
        else:
            resolution = "highest_reliability"
            confidence = min(0.95, 0.5 + (against_score - for_score) * 0.15)
        return ConflictRecord(
            claim=claim,
            sources_for=sources_for,
            sources_against=sources_against,
            resolution=resolution,
            confidence=confidence,
        )

    # Strategy 2: Majority consensus
    if len(sources_for) != len(sources_against):
        resolution = "majority"
        total = len(sources_for) + len(sources_against)
        majority_size = max(len(sources_for), len(sources_against))
        confidence = min(0.85, majority_size / total)
        return ConflictRecord(
            claim=claim,
            sources_for=sources_for,
            sources_against=sources_against,
            resolution=resolution,
            confidence=confidence,
        )

    # Strategy 3: Flag for human review
    return ConflictRecord(
        claim=claim,
        sources_for=sources_for,
        sources_against=sources_against,
        resolution="flagged_for_human",
        confidence=0.3,
    )


def resolve_conflicts(
    conflicts: list[dict],
    reliability_lookup: dict[str, SourceReliability],
) -> list[ConflictRecord]:
    """Resolve all conflicts in a batch.

    Args:
        conflicts: List of dicts with keys: claim, sources_for, sources_against
        reliability_lookup: Map of URL -> SourceReliability

    Returns:
        List of ConflictRecords with resolutions.
    """
    results = []
    for conflict in conflicts:
        record = resolve_conflict(
            claim=conflict["claim"],
            sources_for=conflict.get("sources_for", []),
            sources_against=conflict.get("sources_against", []),
            reliability_lookup=reliability_lookup,
        )
        results.append(record)
    return results
