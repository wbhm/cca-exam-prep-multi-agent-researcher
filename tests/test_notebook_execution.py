"""Headless notebook execution tests.

Tier 2 of the 3-tier notebook-test correlation:
- Uses nbformat to parse notebooks
- Extracts code cells, skips cells tagged 'skip-execution'
- Executes via exec() in shared namespace
- Catches import errors, attribute errors, syntax failures

Matches the sibling project's test_notebook_execution.py pattern.
"""

from __future__ import annotations

import os
from pathlib import Path

import nbformat
import pytest

NOTEBOOKS_DIR = Path(__file__).parent.parent / "notebooks"
PROJECT_ROOT = Path(__file__).parent.parent


def _load_executable_cells(name: str) -> list[str]:
    """Return source of code cells without skip-execution tag."""
    path = NOTEBOOKS_DIR / name
    nb = nbformat.read(path.open(), as_version=4)
    cells = []
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        tags = cell.get("metadata", {}).get("tags", [])
        if "skip-execution" in tags:
            continue
        src = cell.source.strip()
        if src:
            cells.append(src)
    return cells


def _execute_cells(cells: list[str], notebook_name: str) -> None:
    """Execute cells sequentially in a shared namespace."""
    # Set up the namespace with necessary paths
    namespace: dict = {}
    exec(f"import sys; sys.path.insert(0, '{PROJECT_ROOT}')", namespace)
    exec(f"import sys; sys.path.insert(0, '{NOTEBOOKS_DIR}')", namespace)

    # Notebooks run with the notebooks/ directory as cwd; restore it afterwards
    # so the chdir does not leak into the rest of the test session.
    previous_cwd = os.getcwd()
    os.chdir(NOTEBOOKS_DIR)
    try:
        for i, cell in enumerate(cells):
            try:
                exec(cell, namespace)
            except Exception as e:
                pytest.fail(
                    f"Notebook {notebook_name}, cell {i} failed:\n"
                    f"  Error: {type(e).__name__}: {e}\n"
                    f"  Cell source:\n{cell[:200]}"
                )
    finally:
        os.chdir(previous_cwd)


# --- Headless execution for non-API notebooks ---

class TestNotebookExecution:
    """Execute non-API cells from each notebook."""

    def test_00_setup(self):
        cells = _load_executable_cells("00_setup.ipynb")
        _execute_cells(cells, "00_setup")

    def test_01_hub_and_spoke(self):
        cells = _load_executable_cells("01_hub_and_spoke.ipynb")
        _execute_cells(cells, "01_hub_and_spoke")

    def test_02_context_isolation(self):
        cells = _load_executable_cells("02_context_isolation.ipynb")
        _execute_cells(cells, "02_context_isolation")

    def test_03_tool_scoping(self):
        cells = _load_executable_cells("03_tool_scoping.ipynb")
        _execute_cells(cells, "03_tool_scoping")

    def test_04_error_handling(self):
        cells = _load_executable_cells("04_error_handling.ipynb")
        _execute_cells(cells, "04_error_handling")

    def test_05_task_decomposition(self):
        cells = _load_executable_cells("05_task_decomposition.ipynb")
        _execute_cells(cells, "05_task_decomposition")

    def test_06_conflict_resolution(self):
        cells = _load_executable_cells("06_conflict_resolution.ipynb")
        _execute_cells(cells, "06_conflict_resolution")

    def test_07_mcp_primitives(self):
        cells = _load_executable_cells("07_mcp_primitives.ipynb")
        _execute_cells(cells, "07_mcp_primitives")

    def test_08_integration(self):
        cells = _load_executable_cells("08_integration.ipynb")
        _execute_cells(cells, "08_integration")


# --- Cell tagging verification ---

class TestCellTagging:
    """Verify that API-dependent cells are properly tagged."""

    def test_00_setup_has_skip_tag(self):
        """The API key check cell should be tagged skip-execution."""
        path = NOTEBOOKS_DIR / "00_setup.ipynb"
        nb = nbformat.read(path.open(), as_version=4)
        api_cells = [
            cell for cell in nb.cells
            if cell.cell_type == "code" and "ANTHROPIC_API_KEY" in cell.source
        ]
        for cell in api_cells:
            tags = cell.get("metadata", {}).get("tags", [])
            assert "skip-execution" in tags, (
                "API key cell should be tagged skip-execution"
            )
