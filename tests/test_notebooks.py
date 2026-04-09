"""Structural tests for notebooks.

Tier 1 of the 3-tier notebook-test correlation:
- Each notebook file exists
- Each has required markdown sections
- Each imports the correct modules
- Each checks the correct observable metrics

Mirrors the sibling project's test_notebooks.py pattern.
"""

from __future__ import annotations

from pathlib import Path

import nbformat
import pytest

NOTEBOOKS_DIR = Path(__file__).parent.parent / "notebooks"

EXPECTED_NOTEBOOKS = [
    "00_setup.ipynb",
    "01_hub_and_spoke.ipynb",
    "02_context_isolation.ipynb",
    "03_tool_scoping.ipynb",
    "04_error_handling.ipynb",
    "05_task_decomposition.ipynb",
    "06_conflict_resolution.ipynb",
    "07_mcp_primitives.ipynb",
    "08_integration.ipynb",
]


def _read_nb(name: str) -> nbformat.NotebookNode:
    path = NOTEBOOKS_DIR / name
    return nbformat.read(path.open(), as_version=4)


def _get_all_source(nb: nbformat.NotebookNode) -> str:
    """Concatenate all cell sources for text searching."""
    return "\n".join(cell.source for cell in nb.cells)


def _get_markdown_text(nb: nbformat.NotebookNode) -> str:
    """Concatenate all markdown cell sources."""
    return "\n".join(cell.source for cell in nb.cells if cell.cell_type == "markdown")


def _get_code_source(nb: nbformat.NotebookNode) -> str:
    """Concatenate all code cell sources."""
    return "\n".join(cell.source for cell in nb.cells if cell.cell_type == "code")


# --- Existence ---

class TestNotebookExistence:
    @pytest.mark.parametrize("name", EXPECTED_NOTEBOOKS)
    def test_notebook_exists(self, name):
        assert (NOTEBOOKS_DIR / name).exists(), f"Missing notebook: {name}"


# --- Section Structure ---

class TestNotebookSections:
    def test_02_has_anti_pattern_section(self):
        md = _get_markdown_text(_read_nb("02_context_isolation.ipynb"))
        assert "anti-pattern" in md.lower()

    def test_02_has_correct_pattern_section(self):
        md = _get_markdown_text(_read_nb("02_context_isolation.ipynb"))
        assert "correct pattern" in md.lower()

    def test_03_has_anti_pattern_section(self):
        md = _get_markdown_text(_read_nb("03_tool_scoping.ipynb"))
        assert "anti-pattern" in md.lower()

    def test_04_has_anti_pattern_section(self):
        md = _get_markdown_text(_read_nb("04_error_handling.ipynb"))
        assert "anti-pattern" in md.lower()

    @pytest.mark.parametrize("name", [
        "01_hub_and_spoke.ipynb",
        "02_context_isolation.ipynb",
        "03_tool_scoping.ipynb",
        "04_error_handling.ipynb",
        "05_task_decomposition.ipynb",
        "06_conflict_resolution.ipynb",
        "07_mcp_primitives.ipynb",
        "08_integration.ipynb",
    ])
    def test_has_cca_exam_tip(self, name):
        md = _get_markdown_text(_read_nb(name))
        assert "cca exam tip" in md.lower(), f"{name} missing CCA Exam Tip section"


# --- Import Verification ---

class TestNotebookImports:
    def test_02_imports_shared_context(self):
        code = _get_code_source(_read_nb("02_context_isolation.ipynb"))
        assert "from research_agents.anti_patterns.shared_context import run_leaky_subagent" in code

    def test_02_imports_context_builder(self):
        code = _get_code_source(_read_nb("02_context_isolation.ipynb"))
        assert "from research_agents.agent.context_builder import build_subagent_context" in code

    def test_03_imports_super_agent(self):
        code = _get_code_source(_read_nb("03_tool_scoping.ipynb"))
        assert "SUPER_AGENT_TOOLS" in code

    def test_03_imports_from_anti_patterns(self):
        code = _get_code_source(_read_nb("03_tool_scoping.ipynb"))
        assert "from research_agents.anti_patterns.super_agent" in code

    def test_04_imports_silent_failures(self):
        code = _get_code_source(_read_nb("04_error_handling.ipynb"))
        assert "from research_agents.anti_patterns.silent_failures" in code

    def test_04_imports_dispatch(self):
        code = _get_code_source(_read_nb("04_error_handling.ipynb"))
        assert "from research_agents.tools.handlers import dispatch" in code

    def test_06_imports_conflict_resolver(self):
        code = _get_code_source(_read_nb("06_conflict_resolution.ipynb"))
        assert "from research_agents.agent.conflict_resolver import" in code

    def test_08_imports_coordinator(self):
        code = _get_code_source(_read_nb("08_integration.ipynb"))
        assert "from research_agents.agent.coordinator import" in code


# --- Observable Metrics ---

class TestNotebookMetrics:
    def test_02_checks_context_length(self):
        """NB02 must compare context lengths (leaked vs explicit)."""
        code = _get_code_source(_read_nb("02_context_isolation.ipynb"))
        assert "context_length" in code or "len(leaked_context)" in code

    def test_03_checks_tool_count(self):
        """NB03 must compare tool counts (18+ vs 4-5)."""
        code = _get_code_source(_read_nb("03_tool_scoping.ipynb"))
        assert "get_super_agent_tool_count" in code

    def test_04_checks_error_type(self):
        """NB04 must check error_type field presence."""
        code = _get_code_source(_read_nb("04_error_handling.ipynb"))
        assert "error_type" in code

    def test_04_checks_retry_eligible(self):
        """NB04 must check retry_eligible field."""
        code = _get_code_source(_read_nb("04_error_handling.ipynb"))
        assert "retry_eligible" in code

    def test_05_checks_wave_count(self):
        """NB05 must demonstrate parallel waves."""
        code = _get_code_source(_read_nb("05_task_decomposition.ipynb"))
        assert "sort_tasks_into_waves" in code

    def test_06_checks_resolution_strategy(self):
        """NB06 must show resolution strategy."""
        code = _get_code_source(_read_nb("06_conflict_resolution.ipynb"))
        assert "resolution" in code

    def test_08_checks_confidence_score(self):
        """NB08 must report confidence score."""
        code = _get_code_source(_read_nb("08_integration.ipynb"))
        assert "confidence_score" in code

    def test_08_checks_gaps(self):
        """NB08 must report gaps (unavailable sources)."""
        code = _get_code_source(_read_nb("08_integration.ipynb"))
        assert "gaps" in code
