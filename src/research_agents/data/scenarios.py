"""Pre-built research query scenarios with expected outcomes.

Each scenario defines the query, which agents should be involved,
expected number of conflicts, and the expected outcome type.
Used across notebooks for consistent, reproducible comparisons.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchScenario:
    """A pre-defined research scenario for teaching and testing."""

    name: str
    query: str
    expected_agents: list[str]
    expected_conflicts: int
    expected_gaps: int  # sources expected to fail (timeout, 404)
    description: str


SCENARIOS: dict[str, ResearchScenario] = {
    "climate_renewable": ResearchScenario(
        name="climate_renewable",
        query="What is the current state of renewable energy adoption globally?",
        expected_agents=["web_researcher", "data_extractor", "document_analyzer", "fact_checker"],
        expected_conflicts=1,  # Blog claims 45% vs .gov claims 30%
        expected_gaps=0,
        description=(
            "Tests conflict resolution: a low-reliability blog contradicts "
            "a high-reliability government source on renewable energy share."
        ),
    ),
    "ai_healthcare": ResearchScenario(
        name="ai_healthcare",
        query="How is AI being used in healthcare diagnostics?",
        expected_agents=["web_researcher", "document_analyzer", "fact_checker"],
        expected_conflicts=0,
        expected_gaps=1,  # healthtech blog returns 404
        description=(
            "Tests error handling: one source returns 404. The report should "
            "note the gap rather than silently omitting it."
        ),
    ),
    "economic_impact": ResearchScenario(
        name="economic_impact",
        query="What is the economic impact of remote work on productivity?",
        expected_agents=[
            "web_researcher",
            "data_extractor",
            "document_analyzer",
            "fact_checker",
        ],
        expected_conflicts=1,  # Blog says -20% vs McKinsey/Stanford says +13%
        expected_gaps=1,  # timeout.example.com times out
        description=(
            "Tests both conflict resolution AND error handling: contradicting "
            "productivity claims plus a timeout on one source."
        ),
    ),
}
