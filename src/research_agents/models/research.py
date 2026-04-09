"""Pydantic models for the multi-agent research system.

Covers the full lifecycle: research query decomposition, subtask delegation,
source results, conflict tracking, and final report compilation.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class SourceReliability(StrEnum):
    """Source reliability tier used for conflict resolution weighting."""

    HIGH = "high"  # peer-reviewed, .gov, official statistics
    MEDIUM = "medium"  # established news outlets, .edu
    LOW = "low"  # blogs, unverified sources
    UNKNOWN = "unknown"  # reliability not yet assessed


class ResearchQuery(BaseModel):
    """Input to the coordinator: what to research and how deeply."""

    query: str
    depth: str = "standard"  # "quick", "standard", "deep"
    required_sources: int = 3


class SubTask(BaseModel):
    """A single unit of work the coordinator delegates to a subagent.

    CCA Key Concept: The `context` field contains ONLY what the coordinator
    explicitly chose to pass. Subagents do not inherit the coordinator's
    conversation history, system prompt, or other subagents' results.
    """

    task_id: str
    agent_type: str  # "web_researcher", "document_analyzer", "data_extractor", "fact_checker"
    instruction: str  # what to do
    context: str  # explicitly passed context (NOT inherited)
    depends_on: list[str] = Field(default_factory=list)  # task_ids for sequential ordering


class SearchResult(BaseModel):
    """A single web search hit."""

    url: str
    title: str
    snippet: str
    reliability: SourceReliability = SourceReliability.UNKNOWN


class PageContent(BaseModel):
    """Fetched content from a web page."""

    url: str
    title: str
    text: str
    reliability: SourceReliability = SourceReliability.UNKNOWN


class Document(BaseModel):
    """A research document in the document store."""

    doc_id: str
    title: str
    sections: list[DocumentSection] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    reliability: SourceReliability = SourceReliability.MEDIUM


class DocumentSection(BaseModel):
    """A section within a document."""

    heading: str
    content: str
    claims: list[str] = Field(default_factory=list)


class FactRecord(BaseModel):
    """A verified fact from the knowledge base."""

    claim: str
    verified: bool
    confidence: float = Field(ge=0.0, le=1.0)
    source: str
    reliability: SourceReliability = SourceReliability.HIGH


class SourceResult(BaseModel):
    """Aggregated result from a single source, used in the final report."""

    source_url: str
    title: str
    content_summary: str
    reliability: SourceReliability
    claims: list[str] = Field(default_factory=list)


class ConflictRecord(BaseModel):
    """A documented contradiction between sources, with resolution metadata.

    CCA Key Concept: The coordinator must resolve contradictions using
    deterministic strategies (reliability ranking, majority consensus,
    human flag) rather than just picking the first result.
    """

    claim: str
    sources_for: list[str]  # source URLs that support the claim
    sources_against: list[str]  # source URLs that contradict the claim
    resolution: str  # "majority", "highest_reliability", "flagged_for_human"
    confidence: float = Field(ge=0.0, le=1.0)


class ResearchReport(BaseModel):
    """The final output of the coordinator: a synthesized research report.

    CCA Key Concept: The `gaps` field records sources that were unavailable
    (timeouts, errors) so the report is transparent about its limitations.
    A report that says "we could not reach Source X" is more trustworthy
    than one that silently omits it.
    """

    query: str
    findings: list[SourceResult] = Field(default_factory=list)
    conflicts: list[ConflictRecord] = Field(default_factory=list)
    synthesis: str = ""
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    gaps: list[str] = Field(default_factory=list)  # sources that failed/were unavailable


# Needed for forward reference resolution
Document.model_rebuild()
