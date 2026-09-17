"""The documentation stays in step with the code.

Each test pins one claim a document makes to something the code can prove:
quoted signatures, linked paths, resolver arithmetic, and the absence of
names that no longer exist.
"""

from __future__ import annotations

import ast
import inspect
import re
from pathlib import Path

import pytest

from research_agents.agent import agent_loop, conflict_resolver, context_builder, coordinator
from research_agents.anti_patterns import shared_context, silent_failures, super_agent
from research_agents.data.sources import SOURCE_RELIABILITY_RATINGS
from research_agents.models.errors import ToolErrorResponse
from research_agents.models.research import SourceReliability
from research_agents.tools import handlers
from research_agents.tools._errors import error_response

ROOT = Path(__file__).resolve().parent.parent
DOC_NAMES = ("README.md", "TUTORIAL.md", "CLAUDE.md", "docs/tutorial.md")
DOCS = {name: (ROOT / name).read_text(encoding="utf-8") for name in DOC_NAMES}

HIGH = "https://bls.gov/report"
HIGH_2 = "https://energy.gov/data"
HIGH_3 = "https://census.gov/table"
MEDIUM = "https://mckinsey.com/study"
BLOGS = [
    "https://workfromhome-blog.example.com/a",
    "https://workfromhome-blog.example.com/b",
    "https://workfromhome-blog.example.com/c",
]
RATINGS = {
    "bls.gov": SourceReliability.HIGH,
    "energy.gov": SourceReliability.HIGH,
    "census.gov": SourceReliability.HIGH,
    "mckinsey.com": SourceReliability.MEDIUM,
    "workfromhome-blog.example.com": SourceReliability.LOW,
}


# --- hard-coded counts and dead names ---------------------------------------


@pytest.mark.parametrize("name", ("README.md", "TUTORIAL.md", "CLAUDE.md"))
def test_no_hard_coded_test_count(name: str) -> None:
    hits = re.findall(r"\b\d+\s+tests\b", DOCS[name], flags=re.IGNORECASE)
    assert hits == [], f"{name} hard-codes a test count: {hits}"


@pytest.mark.parametrize("name", DOC_NAMES)
def test_docs_name_no_missing_model(name: str) -> None:
    assert "VerificationResult" not in DOCS[name]


@pytest.mark.parametrize("name", DOC_NAMES)
def test_docs_do_not_claim_a_resource_uri_scheme(name: str) -> None:
    for line in DOCS[name].splitlines():
        if "resource://" in line:
            assert "no special" in line, f"{name} presents resource:// as an MCP convention"


# --- links -------------------------------------------------------------------


_LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


@pytest.mark.parametrize("name", ("README.md", "TUTORIAL.md"))
def test_relative_links_point_at_existing_paths(name: str) -> None:
    missing = []
    for target in _LINK.findall(DOCS[name]):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if not (ROOT / target).exists():
            missing.append(target)
    assert missing == [], f"{name} links to paths that do not exist: {missing}"


# --- resolver arithmetic the tutorials describe -----------------------------


def test_tie_on_tier_falls_to_majority_against() -> None:
    """TUTORIAL.md NB06: 2 HIGH for, 3 HIGH against -> majority, against, 0.6."""
    record = conflict_resolver.resolve_conflict(
        "claim", [HIGH, HIGH_2], [HIGH_3, HIGH, HIGH_2], RATINGS
    )
    assert record.resolution == "majority"
    assert record.winning_side == "against"
    assert record.confidence == pytest.approx(0.6)


def test_tie_on_tier_and_count_is_flagged() -> None:
    """TUTORIAL.md NB06: 2 vs 2 at the same tier -> flagged_for_human."""
    record = conflict_resolver.resolve_conflict("claim", [HIGH, HIGH_2], [HIGH_3, HIGH], RATINGS)
    assert record.resolution == "flagged_for_human"
    assert record.winning_side == "undecided"
    assert record.confidence == pytest.approx(0.3)


def test_one_gov_source_outranks_three_blogs() -> None:
    """TUTORIAL.md NB06 and README: best tier per side, never a sum."""
    record = conflict_resolver.resolve_conflict("claim", BLOGS, [HIGH], RATINGS)
    assert record.resolution == "highest_reliability"
    assert record.winning_side == "against"
    assert record.confidence == pytest.approx(0.5 + 2 * 0.15)


def test_three_medium_versus_one_medium_is_majority_075() -> None:
    """docs/tutorial.md section 11: 3 of 4 -> 0.75."""
    record = conflict_resolver.resolve_conflict("claim", [MEDIUM] * 3, [MEDIUM], RATINGS)
    assert record.resolution == "majority"
    assert record.confidence == pytest.approx(0.75)


def test_walkthrough_conflict_resolves_for_with_080() -> None:
    """docs/tutorial.md section 16 uses the real domain-keyed ratings."""
    record = conflict_resolver.resolve_conflict(
        "Remote workers are more productive",
        ["https://mckinsey.com/remote-work-2024", "https://bls.gov/remote-work-stats"],
        ["https://workfromhome-blog.example.com/remote-bad"],
        SOURCE_RELIABILITY_RATINGS,
    )
    assert (record.resolution, record.winning_side) == ("highest_reliability", "for")
    assert record.confidence == pytest.approx(0.80)


def test_tutorial_checklist_names_real_error_fields() -> None:
    """TUTORIAL.md checklist lists ToolErrorResponse fields; each must exist."""
    line = next(ln for ln in DOCS["TUTORIAL.md"].splitlines() if "I can list the fields" in ln)
    named = set(re.findall(r"`(\w+)`", line)) - {"ToolErrorResponse"}
    assert named <= set(ToolErrorResponse.model_fields)
    assert ToolErrorResponse.model_validate_json(error_response("timeout", "x", "y"))


# --- quoted signatures match the source -------------------------------------


PUBLIC = {
    "build_subagent_context": context_builder.build_subagent_context,
    "run_agent_loop": agent_loop.run_agent_loop,
    "sort_tasks_into_waves": coordinator.sort_tasks_into_waves,
    "run_coordinator": coordinator.run_coordinator,
    "collect_tool_errors": coordinator.collect_tool_errors,
    "collect_gaps": coordinator.collect_gaps,
    "build_research_report": coordinator.build_research_report,
    "resolve_conflicts": conflict_resolver.resolve_conflicts,
    "dispatch": handlers.dispatch,
    "error_response": error_response,
    "run_leaky_subagent": shared_context.run_leaky_subagent,
    "silent_dispatch": silent_failures.silent_dispatch,
    "super_agent_dispatch": super_agent.super_agent_dispatch,
}


def _quoted_defs(text: str) -> list[tuple[str, str]]:
    """Every top-level ``def name(...)`` header in the document, joined until its colon."""
    lines = text.splitlines()
    found: list[tuple[str, str]] = []
    for i, line in enumerate(lines):
        match = re.match(r"def (\w+)\(", line)
        if not match:
            continue
        header = [line]
        j = i
        while not header[-1].split("#")[0].rstrip().endswith(":"):
            j += 1
            header.append(lines[j])
        found.append((match.group(1), "\n".join(header)))
    return found


def _doc_params(header: str) -> list[tuple[str, str | None]]:
    tree = ast.parse(header + "\n    pass")
    args = tree.body[0].args
    positional = args.posonlyargs + args.args
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    out = [(a.arg, ast.unparse(d) if d is not None else None) for a, d in zip(positional, defaults)]
    out += [
        (a.arg, ast.unparse(d) if d is not None else None)
        for a, d in zip(args.kwonlyargs, args.kw_defaults)
    ]
    return out


def _real_params(fn: object) -> list[tuple[str, str | None]]:
    out = []
    for p in inspect.signature(fn).parameters.values():
        if p.default is inspect.Parameter.empty:
            out.append((p.name, None))
        elif callable(p.default):
            out.append((p.name, p.default.__name__))
        else:
            out.append((p.name, repr(p.default)))
    return out


def test_every_public_function_is_quoted() -> None:
    quoted = {name for name, _ in _quoted_defs(DOCS["docs/tutorial.md"])}
    assert set(PUBLIC) <= quoted, f"docs/tutorial.md does not quote: {set(PUBLIC) - quoted}"


@pytest.mark.parametrize(
    ("name", "header"),
    [(n, h) for n, h in _quoted_defs(DOCS["docs/tutorial.md"]) if n in PUBLIC],
    ids=lambda v: v if isinstance(v, str) and "\n" not in v else "",
)
def test_quoted_signature_matches_source(name: str, header: str) -> None:
    assert _doc_params(header) == _real_params(PUBLIC[name]), header


# --- quoted signatures in notebook markdown -----------------------------------

NOTEBOOKS = sorted((ROOT / "notebooks").glob("0*.ipynb"))

# Anti-pattern sketches the notebooks quote on purpose; they exist nowhere in the package.
PSEUDOCODE = {"run_web_researcher"}


def _notebook_quoted_defs() -> list[tuple[str, str, str]]:
    """(notebook name, function name, header) for every def quoted in a markdown cell."""
    import nbformat

    found = []
    for path in NOTEBOOKS:
        nb = nbformat.read(path, as_version=4)
        for cell in nb.cells:
            if cell.cell_type != "markdown":
                continue
            for name, header in _quoted_defs(cell.source):
                found.append((path.name, name, header))
    return found


def test_every_notebook_quoted_def_is_a_known_function() -> None:
    unknown = {
        (nb, name)
        for nb, name, _ in _notebook_quoted_defs()
        if name not in PUBLIC and name not in PSEUDOCODE
    }
    assert unknown == set(), f"notebooks quote functions the test cannot check: {unknown}"


@pytest.mark.parametrize(
    ("notebook", "name", "header"),
    [(nb, n, h) for nb, n, h in _notebook_quoted_defs() if n in PUBLIC],
    ids=lambda v: v if isinstance(v, str) and "\n" not in v else "",
)
def test_notebook_quoted_signature_matches_source(notebook: str, name: str, header: str) -> None:
    assert _doc_params(header) == _real_params(PUBLIC[name]), f"{notebook}: {header}"
