"""Shared source-reliability matching.

Reliability ratings are keyed by domain ("energy.gov") while subagents report
full URLs ("https://energy.gov/renewable-2024"). Every consumer of a ratings
map (the knowledge base, the conflict resolver) must apply the same matching
rule, so it lives here rather than being re-implemented per caller.
"""

from __future__ import annotations

from research_agents.models.research import SourceReliability


def match_reliability(
    url: str,
    ratings: dict[str, SourceReliability],
) -> SourceReliability:
    """Return the rating for ``url``: exact key first, then domain containment.

    "Domain containment" means the known key appears inside the URL
    (``"energy.gov" in "https://energy.gov/page"``) or vice versa. Unknown
    sources rate UNKNOWN, which the resolver scores as 0.
    """
    if url in ratings:
        return ratings[url]
    for known, reliability in ratings.items():
        if known in url or url in known:
            return reliability
    return SourceReliability.UNKNOWN
