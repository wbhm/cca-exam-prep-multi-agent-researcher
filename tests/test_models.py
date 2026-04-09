"""Tests for Pydantic models in research_agents.models."""

from __future__ import annotations

import json

from research_agents.models.errors import SilentFailureResponse, ToolErrorResponse
from research_agents.models.research import (
    ConflictRecord,
    Document,
    DocumentSection,
    FactRecord,
    PageContent,
    ResearchQuery,
    ResearchReport,
    SearchResult,
    SourceReliability,
    SourceResult,
    SubTask,
)


# --- SourceReliability ---

class TestSourceReliability:
    def test_values(self):
        assert SourceReliability.HIGH == "high"
        assert SourceReliability.MEDIUM == "medium"
        assert SourceReliability.LOW == "low"
        assert SourceReliability.UNKNOWN == "unknown"

    def test_all_values(self):
        assert len(SourceReliability) == 4


# --- ResearchQuery ---

class TestResearchQuery:
    def test_defaults(self):
        q = ResearchQuery(query="test")
        assert q.depth == "standard"
        assert q.required_sources == 3

    def test_custom(self):
        q = ResearchQuery(query="test", depth="deep", required_sources=5)
        assert q.depth == "deep"
        assert q.required_sources == 5


# --- SubTask ---

class TestSubTask:
    def test_minimal(self):
        t = SubTask(task_id="t1", agent_type="web_researcher", instruction="search", context="ctx")
        assert t.depends_on == []

    def test_with_dependencies(self):
        t = SubTask(
            task_id="t2",
            agent_type="fact_checker",
            instruction="verify",
            context="claims from t1",
            depends_on=["t1"],
        )
        assert t.depends_on == ["t1"]

    def test_serialization(self):
        t = SubTask(task_id="t1", agent_type="web_researcher", instruction="go", context="ctx")
        data = json.loads(t.model_dump_json())
        assert data["task_id"] == "t1"
        assert data["agent_type"] == "web_researcher"


# --- SearchResult ---

class TestSearchResult:
    def test_defaults(self):
        r = SearchResult(url="http://example.com", title="Test", snippet="snip")
        assert r.reliability == SourceReliability.UNKNOWN


# --- Document ---

class TestDocument:
    def test_with_sections(self):
        sec = DocumentSection(heading="Intro", content="text", claims=["claim1"])
        doc = Document(doc_id="d1", title="Doc", sections=[sec])
        assert len(doc.sections) == 1
        assert doc.sections[0].claims == ["claim1"]


# --- FactRecord ---

class TestFactRecord:
    def test_confidence_bounds(self):
        f = FactRecord(claim="test", verified=True, confidence=0.95, source="src")
        assert 0 <= f.confidence <= 1


# --- ConflictRecord ---

class TestConflictRecord:
    def test_structure(self):
        c = ConflictRecord(
            claim="test claim",
            sources_for=["src1"],
            sources_against=["src2"],
            resolution="majority",
            confidence=0.8,
        )
        assert c.resolution == "majority"


# --- ResearchReport ---

class TestResearchReport:
    def test_defaults(self):
        r = ResearchReport(query="test")
        assert r.findings == []
        assert r.conflicts == []
        assert r.gaps == []
        assert r.synthesis == ""
        assert r.confidence_score == 0.0

    def test_with_gaps(self):
        r = ResearchReport(
            query="test",
            gaps=["Source X was unavailable"],
            confidence_score=0.7,
        )
        assert len(r.gaps) == 1


# --- ToolErrorResponse ---

class TestToolErrorResponse:
    def test_structure(self):
        e = ToolErrorResponse(
            error_type="timeout",
            source="api.example.com",
            message="Timed out",
            retry_eligible=True,
            fallback_available=False,
        )
        assert e.status == "error"
        assert e.retry_eligible is True
        assert e.partial_data is None

    def test_serialization(self):
        e = ToolErrorResponse(
            error_type="not_found",
            source="example.com",
            message="404",
            retry_eligible=False,
            fallback_available=False,
        )
        data = json.loads(e.model_dump_json())
        assert data["status"] == "error"
        assert data["error_type"] == "not_found"


# --- SilentFailureResponse ---

class TestSilentFailureResponse:
    def test_anti_pattern(self):
        """Silent failure returns success with null data — the anti-pattern."""
        s = SilentFailureResponse()
        assert s.status == "success"
        assert s.data is None

    def test_indistinguishable_from_empty(self):
        """This is the whole problem: you can't tell failure from empty."""
        data = json.loads(s.model_dump_json()) if (s := SilentFailureResponse()) else {}
        assert data["status"] == "success"
        assert data["data"] is None
