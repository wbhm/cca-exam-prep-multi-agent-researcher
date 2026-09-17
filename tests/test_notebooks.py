"""Structural tests for notebooks.

Tier 1 of the 3-tier notebook-test correlation:
- Each notebook file exists
- Each has required markdown sections
- Each imports the correct modules
- Each checks the correct observable metrics

Mirrors the sibling project's test_notebooks.py pattern.
"""

from __future__ import annotations

import importlib.util
import re
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


# --- Fixed constructs present, broken constructs absent ---
#
# Each notebook used to assert its conclusion (literal True/False in the
# comparison table) or tell a story the cells did not execute. These tests pin
# the repaired shape: the demonstration must be measured, and the old shortcut
# must not creep back in.

class TestNotebookDemonstrationsAreMeasured:
    def test_00_loads_dotenv_before_reading_key(self):
        nb = _read_nb("00_setup.ipynb")
        key_cells = [c.source for c in nb.cells if c.cell_type == "code" and "ANTHROPIC_API_KEY" in c.source]
        assert key_cells and all("load_dotenv" in c for c in key_cells)
        md = _get_markdown_text(nb)
        assert "mock mode" not in md.lower()

    def test_01_shows_why_sideways_calls_fail(self):
        code = _get_code_source(_read_nb("01_hub_and_spoke.ipynb"))
        assert "dataclasses.fields(ServiceContainer)" in code
        assert "sideways_call_refused" in code

    def test_02_replays_leaky_subagent_through_real_loop(self):
        code = _get_code_source(_read_nb("02_context_isolation.ipynb"))
        assert "run_leaky_subagent(" in code, "anti-pattern must be executed, not inlined"
        assert "client.calls[0]" in code, "metrics must be read from what was sent"
        assert "'contains_coordinator_reasoning': True" not in code
        assert "free_of_coordinator_reasoning" in code

    def test_02_shows_the_forgot_to_forward_case(self):
        code = _get_code_source(_read_nb("02_context_isolation.ipynb"))
        assert "forgot_context" in code

    def test_03_replays_out_of_scope_call_through_both_routers(self):
        nb = _read_nb("03_tool_scoping.ipynb")
        code = _get_code_source(nb)
        assert "super_agent_dispatch" in code
        assert "out_of_scope_call_blocked" in code
        assert "'tools_per_agent': 4" not in code
        assert "total_tools" not in code
        assert "20" in _get_markdown_text(nb), "super agent has 20 tools, say so"

    def test_04_executes_the_cascade(self):
        code = _get_code_source(_read_nb("04_error_handling.ipynb"))
        assert "silent_dispatch" in code
        assert "collect_gaps" in code or "build_research_report" in code
        assert "'coordinator_can_retry': False" not in code
        assert "gaps_reported" in code

    def test_05_compares_wave_counts(self):
        nb = _read_nb("05_task_decomposition.ipynb")
        assert "wave_count" in _get_code_source(nb)
        assert "4x" not in _get_markdown_text(nb)

    def test_06_has_first_result_wins_anti_pattern(self):
        nb = _read_nb("06_conflict_resolution.ipynb")
        code = _get_code_source(nb)
        assert "first_result_wins" in code
        assert "winning_side" in code
        assert "order_independent" in code
        assert "Sum reliability" not in _get_markdown_text(nb)

    def test_07_uses_spec_vocabulary_and_calls_the_resources(self):
        nb = _read_nb("07_mcp_primitives.ipynb")
        src = _get_all_source(nb)
        assert "VerificationResult" not in src
        assert "resource://" not in src
        assert "application" in _get_markdown_text(nb).lower()
        code = _get_code_source(nb)
        for call in ("get_source_reliability(", "list_documents(", "get_schema(", "dispatch("):
            assert call in code, f"NB07 must execute {call}"

    def test_08_derives_gaps_and_conflicts_from_tool_results(self):
        code = _get_code_source(_read_nb("08_integration.ipynb"))
        assert "scripted_client" in code
        assert "collect_gaps" in code
        assert "flag_conflict" in code
        assert "winning_side" in code
        assert "gaps=[" not in code, "gaps must come from tool errors, not a literal"

    @pytest.mark.parametrize("name", EXPECTED_NOTEBOOKS)
    def test_no_notebook_imports_from_tests_package(self, name):
        assert "from tests." not in _get_code_source(_read_nb(name))

    @pytest.mark.parametrize("name", EXPECTED_NOTEBOOKS)
    def test_no_notebook_calls_the_api(self, name):
        code = _get_code_source(_read_nb(name))
        statements = "\n".join(
            line for line in code.splitlines() if not line.lstrip().startswith("#")
        )
        assert "anthropic.Anthropic(" not in statements
        assert "import anthropic" not in statements


# --- compare_results hygiene ---

_COMPARE_CALL = re.compile(r"compare_results\((.*?)\n\s*\)", re.DOTALL)
_BOOL_LITERAL = re.compile(r"'[a-z_]+':\s*(True|False)\b")
_NEGATIVE_KEY = re.compile(r"'(contains_|leaks_|missing_|lacks_|silent_)[a-z_]*':")


class TestCompareResultsHygiene:
    """Boolean rows must be measured and positively phrased.

    ``compare_results`` labels a bool change FIXED when the correct value is
    True, so a metric named for the defect ("contains_reasoning") prints
    REGRESSED when the fix works. And a literal True/False is an assertion
    dressed as a measurement.
    """

    @pytest.mark.parametrize("name", EXPECTED_NOTEBOOKS)
    def test_no_literal_bools_in_comparisons(self, name):
        code = _get_code_source(_read_nb(name))
        for call in _COMPARE_CALL.findall(code):
            assert not _BOOL_LITERAL.search(call), f"{name}: literal bool in compare_results: {call[:120]}"

    @pytest.mark.parametrize("name", EXPECTED_NOTEBOOKS)
    def test_no_defect_phrased_bool_keys(self, name):
        code = _get_code_source(_read_nb(name))
        for call in _COMPARE_CALL.findall(code):
            assert not _NEGATIVE_KEY.search(call), f"{name}: defect-phrased metric key in {call[:120]}"


# --- Generator sync ---

def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generate_notebooks", Path(__file__).parent.parent / "scripts" / "generate_notebooks.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _shape(nb: nbformat.NotebookNode) -> list[tuple]:
    return [
        (c.cell_type, c.source, tuple(c.get("metadata", {}).get("tags", [])))
        for c in nb.cells
    ]


@pytest.mark.parametrize("name", EXPECTED_NOTEBOOKS)
def test_notebooks_match_generator(name):
    """The committed notebook must equal what scripts/generate_notebooks.py produces."""
    generated = _load_generator().build_all()[name]
    assert _shape(_read_nb(name)) == _shape(generated), (
        f"{name} drifted from the generator; run scripts/generate_notebooks.py"
    )
