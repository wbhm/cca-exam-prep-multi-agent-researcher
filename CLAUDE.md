# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

A hands-on coding example for the CCA (Claude Certified Architect) Foundations Exam -- the **Multi-Agent Research System** scenario. This scenario draws from the three heaviest exam domains simultaneously (Agentic Architecture 27%, Tool Design & MCP 18%, Context Management & Reliability 15% = **60% of exam weight**) and is the scenario that separates strong candidates from average ones.

The project pairs Jupyter notebooks (teaching) with a production Python package. Each notebook demonstrates a CCA anti-pattern side-by-side with the correct architectural pattern. The `anthropic` SDK is used directly (not the Agent SDK) because the CCA concepts require explicit control over context isolation, tool scoping, and the coordinator loop.

## Build and Run Commands

```bash
poetry install --with notebooks             # install all deps including Jupyter
poetry run pytest                           # run all tests (no API key needed)
poetry run pytest tests/test_coordinator.py # single test file
poetry run pytest -k "isolation"            # tests matching a pattern
poetry run ruff check src/                  # lint
poetry run ruff format src/                 # format
poetry run jupyter lab                      # launch notebooks
poetry run python scripts/generate_notebooks.py  # regenerate notebooks from code
task verify                                 # full verification suite (tests + lint + import)
```

## Architecture

### Two-layer design: notebooks + package

**Notebooks** (`notebooks/00-08`): Teaching artifacts generated programmatically via `scripts/generate_notebooks.py`; edit the generator, never the `.ipynb`, and regenerate (`test_notebooks_match_generator` fails otherwise). Notebooks 01-08 follow: setup -> anti-pattern -> observation -> correct pattern -> `compare_results()` -> CCA Exam Tip. No notebook calls the Claude API: demonstrations replay scripted transcripts (`research_agents/testing.py`) through the real loop. The only `skip-execution` cell is the optional `.env`/key check in notebook 00. Every `compare_results()` value must be measured from a run, and boolean metrics must be phrased as properties the fix has (`free_of_x`, not `contains_x`), because the helper labels a True correct value FIXED.

**Package** (`src/research_agents/`): Production implementation with correct patterns only.

### Critical data flow: the coordinator's 6-step orchestration

```
Research query
  -> the caller decomposes it into SubTasks with depends_on fields (no decomposition code in the package)
  -> sort_tasks_into_waves() topologically sorts into parallel waves
  -> for each wave: context_builder.py builds EXPLICIT context string
  -> run_agent_loop() calls the client with SCOPED tools per agent type and logs every tool result
  -> handlers.py dispatches tool calls via DISPATCH[agent_type][tool_name] (dispatch_fn is injectable)
  -> conflict_resolver.py resolves contradictions DETERMINISTICALLY and records winning_side
  -> collect_gaps() derives gaps from structured tool errors; build_research_report() compiles findings, conflicts, gaps
```

### How context isolation is enforced

`context_builder.build_subagent_context(task, predecessor_results)` is the only way `run_coordinator` builds subagent input (`run_agent_loop` itself accepts any string, which is the door the `shared_context` anti-pattern walks through). It accepts a `SubTask` (which contains only explicitly-selected context) and optionally predecessor results filtered by `depends_on`. The coordinator's message history, system prompt, and other subagents' results are structurally unreachable -- they are never arguments to this function.

### How tool scoping works

`tools/definitions.py` defines 5 constants (`WEB_RESEARCHER_TOOLS`, `DOCUMENT_ANALYZER_TOOLS`, etc.) with 4 tools each. `agent/subagents.py` maps agent types to `SubagentConfig(system_prompt, tools)`. When the coordinator delegates, it passes `config.tools` to `run_agent_loop()`. The dispatch registry in `handlers.py` is a nested dict, `DISPATCH[agent_type][tool_name]`, so an out-of-scope call gets a structured `invalid_input` error rather than a handler. Every tool description includes negative bounds ("does NOT...") to prevent misrouting.

### How the 3-tier notebook-test correlation works

1. **Structural** (`test_notebooks.py`): Verifies each notebook exists, has required sections (Anti-Pattern, Correct Pattern, CCA Exam Tip), imports the correct modules, checks the correct observable metrics, contains no literal booleans in `compare_results()`, and matches the generator's output
2. **Headless execution** (`test_notebook_execution.py`): Parses notebooks via `nbformat`, skips `skip-execution` tagged cells, executes remaining cells via `exec()` in shared namespace
3. **Anti-pattern module tests** (`test_anti_patterns.py`): Verifies anti-patterns are wrong in the right way -- `SUPER_AGENT_TOOLS` has 20 tools and `super_agent_dispatch` executes out-of-scope calls, `silent_dispatch` returns `{"status":"success","data":null}`, shared context passes raw messages

`tests/test_docs.py` keeps README, TUTORIAL.md, CLAUDE.md and docs/tutorial.md honest: no hard-coded test counts, linked paths exist, quoted signatures match the source, and the resolver arithmetic the tutorials describe is simulated.

### CCA exam mapping: what each module teaches

| CCA Exam Concept | Module | Anti-Pattern | Exam Question Pattern |
|---|---|---|---|
| Hub-and-spoke | `coordinator.py` | N/A | "What architecture for multi-agent?" -> single coordinator delegating |
| Context isolation | `context_builder.py` | `shared_context.py` | "Subagent ignores instructions" -> context not explicitly passed |
| Tool scoping (4-5) | `definitions.py` | `super_agent.py` | "Agent picks wrong tool" -> decompose into 4-5 tools per agent |
| Structured errors | `ToolErrorResponse` | `silent_failures.py` | "Report missing data" -> require structured error context |
| Conflict resolution | `conflict_resolver.py` | First-result-wins (notebook 06 cell) | "Contradicting sources" -> best-tier reliability ranking, then majority, then human flag |
| Task decomposition | `sort_tasks_into_waves()` | All-sequential | "Parallel or sequential?" -> check data dependencies |
| MCP primitives | Notebook 07 | N/A | "Source reliability DB" -> Resource, not Tool |

## Key design rules

1. **Stop-reason driven loop**: `agent_loop.py` branches on `response.stop_reason`, not on content block types. `tool_use` dispatches; every other stop reason (`end_turn`, `max_tokens`, `refusal`, `pause_turn`, ...) extracts text and exits; exhausting the loop records `stop_reason="max_iterations"`, which `collect_gaps` reports. Tool result blocks carry `is_error` when the handler returned a structured error.
2. **Tool handlers always return JSON strings**: Success or structured error -- never raise exceptions to the caller. Errors are built only through `tools/_errors.error_response()`, so the wire format cannot drift from `ToolErrorResponse`.
3. **Deterministic conflict resolution**: `conflict_resolver.py` uses programmatic rules (best reliability tier per side, majority vote, human flag) and records `winning_side`, not LLM judgment. CCA principle: programmatic enforcement beats prompt-based guidance.
4. **Services via injection**: All tool handlers receive `ServiceContainer`, never import services directly.
5. **Simulated data is deterministic**: All services use pre-built in-memory data from `data/sources.py` (`make_default_services()` builds the container). Some URLs intentionally timeout or 404 to trigger error handling. Some sources have contradicting claims to trigger conflict resolution. `WebSearchService.search` matches an index key only when it is a substring of the query, so scripted `search_web` calls must contain a key such as `"remote work economic"`.
6. **Scripted transcripts, never live calls**: `research_agents/testing.py` (`scripted_client`, `text_turn`, `tool_turn`) is the one mock shared by tests and notebooks. Replay the same transcript through two routers to isolate a single variable.

## Anti-patterns directory

`src/research_agents/anti_patterns/` contains deliberately wrong implementations imported only by notebooks. They intentionally violate the architecture rules above -- that is their purpose. Do not "fix" anti-pattern code to match project standards.
