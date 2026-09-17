"""Tool handlers for the Fact Checker agent."""

from __future__ import annotations

import json

from research_agents.services.container import ServiceContainer
from research_agents.tools._errors import error_response


def handle_verify_claim(input_dict: dict, services: ServiceContainer) -> str:
    claim = input_dict.get("claim", "")
    if not claim:
        return error_response(
            "invalid_input",
            "verify_claim",
            "claim parameter is required",
        )
    facts = services.knowledge_base.lookup_fact(claim)
    if not facts:
        return json.dumps({
            "status": "success",
            "data": {
                "claim": claim,
                "verified": None,
                "confidence": 0.0,
                "message": "No matching facts found in knowledge base",
            },
        })
    # lookup_fact returns the closest-matching record first
    best = facts[0]
    return json.dumps({
        "status": "success",
        "data": {
            "claim": claim,
            "verified": best.verified,
            "confidence": best.confidence,
            "source": best.source,
            "reliability": best.reliability.value,
        },
    })


def handle_cross_reference(input_dict: dict, services: ServiceContainer) -> str:
    claim = input_dict.get("claim", "")
    sources = input_dict.get("sources", [])
    if not claim:
        return error_response(
            "invalid_input",
            "cross_reference",
            "claim parameter is required",
        )
    # Check reliability of each source
    source_ratings = {}
    for url in sources:
        reliability = services.knowledge_base.get_source_reliability(url)
        source_ratings[url] = reliability.value

    # Look up the claim in the knowledge base
    facts = services.knowledge_base.lookup_fact(claim)
    verified_status = None
    if facts:
        verified_status = facts[0].verified

    return json.dumps({
        "status": "success",
        "data": {
            "claim": claim,
            "source_ratings": source_ratings,
            "knowledge_base_verified": verified_status,
            "sources_checked": len(sources),
        },
    })


def handle_score_reliability(input_dict: dict, services: ServiceContainer) -> str:
    url = input_dict.get("url", "")
    if not url:
        return error_response(
            "invalid_input",
            "score_reliability",
            "url parameter is required",
        )
    reliability = services.knowledge_base.get_source_reliability(url)
    return json.dumps({
        "status": "success",
        "data": {"url": url, "reliability": reliability.value},
    })


def handle_flag_conflict(input_dict: dict, services: ServiceContainer) -> str:
    claim = input_dict.get("claim", "")
    sources_for = input_dict.get("sources_for", [])
    sources_against = input_dict.get("sources_against", [])
    if not claim:
        return error_response(
            "invalid_input",
            "flag_conflict",
            "claim parameter is required",
        )
    # Score reliability of all sources involved
    for_ratings = {
        url: services.knowledge_base.get_source_reliability(url).value for url in sources_for
    }
    against_ratings = {
        url: services.knowledge_base.get_source_reliability(url).value for url in sources_against
    }
    return json.dumps({
        "status": "success",
        "data": {
            "claim": claim,
            "sources_for": sources_for,
            "sources_against": sources_against,
            "for_reliability": for_ratings,
            "against_reliability": against_ratings,
            "conflict_flagged": True,
        },
    })
