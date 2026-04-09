# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

A hands-on coding example for the CCA (Claude Certified Architect) Foundations Exam -- the **Multi-Agent Research System** scenario. This scenario draws from the three heaviest exam domains simultaneously (Agentic Architecture 27%, Tool Design & MCP 18%, Context Management & Reliability 15% = **60% of exam weight**) and is the scenario that separates strong candidates from average ones.

The project pairs Jupyter notebooks (teaching) with a production Python package. Each notebook demonstrates a CCA anti-pattern side-by-side with the correct architectural pattern. The `anthropic` SDK is used directly (not the Agent SDK) because the CCA concepts require explicit control over context isolation, tool scoping, and the coordinator loop.

## Build and Run Commands

```bash
poetry install --with notebooks             # install all deps including Jupyter
poetry run pytest                           # run all 180 tests (no API key needed)
poetry run pytest tests/test_coordinator.py # single test file
poetry run pytest -k "test_isolation"       # tests matching a pattern
poetry run ruff check src/                  # lint
poetry run ruff format src/                 # format
poetry run jupyter lab                      # launch notebooks
poetry run python scripts/generate_notebooks.py  # regenerate notebooks from code
task verify                                 # full verification suite (tests + lint + import)
```

## Architecture

### Two-layer design: notebooks + package

**Notebooks** (`notebooks/00-08`): Teaching artifacts generated programmatically via `scripts/generate_notebooks.py`. Each follows: setup -> anti-pattern -> observation -> correct pattern -> `compare_results()` -> CCA Exam Tip. API-dependent cells tagged `skip-execution` for headless testing.

**Package** (`src/research_agents/`): Production implementation with correct patterns only.

### Critical data flow: the coordinator's 6-step orchestration

```
Research query
  -> coordinator.py decomposes into SubTasks with depends_on fields
  -> sort_tasks_into_waves() topologically sorts into parallel waves
  -> for each wave: context_builder.py builds EXPLICIT context string
  -> run_agent_loop() calls Claude API with SCOPED tools per agent type
  -> handlers.py dispatches tool calls via DISPATCH[agent_type][tool_name]
  -> conflict_resolver.py resolves contradictions DETERMINISTICALLY
  -> build_research_report() compiles findings, conflicts, gaps
```

### How context isolation is enforced

`context_builder.build_subagent_context(task, predecessor_results)` is the ONLY way to create subagent input. It accepts a `SubTask` (which contains only explicitly-selected context) and optionally predecessor results filtered by `depends_on`. The coordinator's message history, system prompt, and other subagents' results are structurally unreachable -- they are never arguments to this function.

### How tool scoping works

`tools/definitions.py` defines 5 constants (`WEB_RESEARCHER_TOOLS`, `DOCUMENT_ANALYZER_TOOLS`, etc.) with 4 tools each. `agent/subagents.py` maps agent types to `SubagentConfig(system_prompt, tools)`. When the coordinator delegates, it passes `config.tools` to `run_agent_loop()`. The dispatch registry in `handlers.py` is keyed by `(agent_type, tool_name)`, so tools are isolated per agent even if names overlap. Every tool description includes negative bounds ("does NOT...") to prevent misrouting.

### How the 3-tier notebook-test correlation works

1. **Structural** (`test_notebooks.py`): Verifies each notebook exists, has required sections (Anti-Pattern, Correct Pattern, CCA Exam Tip), imports the correct modules, and checks the correct observable metrics
2. **Headless execution** (`test_notebook_execution.py`): Parses notebooks via `nbformat`, skips `skip-execution` tagged cells, executes remaining cells via `exec()` in shared namespace
3. **Anti-pattern module tests** (`test_anti_patterns.py`): Verifies anti-patterns are wrong in the right way -- `SUPER_AGENT_TOOLS` has 18+ tools, silent handlers return `{"status":"success","data":null}`, shared context passes raw messages

### CCA exam mapping: what each module teaches

| CCA Exam Concept | Module | Anti-Pattern | Exam Question Pattern |
|---|---|---|---|
| Hub-and-spoke | `coordinator.py` | N/A | "What architecture for multi-agent?" -> single coordinator delegating |
| Context isolation | `context_builder.py` | `shared_context.py` | "Subagent ignores instructions" -> context not explicitly passed |
| Tool scoping (4-5) | `definitions.py` | `super_agent.py` | "Agent picks wrong tool" -> decompose into 4-5 tools per agent |
| Structured errors | `ToolErrorResponse` | `silent_failures.py` | "Report missing data" -> require structured error context |
| Conflict resolution | `conflict_resolver.py` | First-result-wins | "Contradicting sources" -> reliability ranking + majority |
| Task decomposition | `sort_tasks_into_waves()` | All-sequential | "Parallel or sequential?" -> check data dependencies |
| MCP primitives | Notebook 07 | N/A | "Source reliability DB" -> Resource, not Tool |

## Key design rules

1. **Stop-reason driven loop**: `agent_loop.py` checks `response.stop_reason`, never content block types. `end_turn` exits, `tool_use` dispatches.
2. **Tool handlers always return JSON strings**: Success or structured error -- never raise exceptions to the caller. `ToolErrorResponse` schema on failure.
3. **Deterministic conflict resolution**: `conflict_resolver.py` uses programmatic rules (reliability scoring, majority vote, human flag), not LLM judgment. CCA principle: programmatic enforcement beats prompt-based guidance.
4. **Services via injection**: All tool handlers receive `ServiceContainer`, never import services directly.
5. **Simulated data is deterministic**: All services use pre-built in-memory data from `data/sources.py`. Some URLs intentionally timeout or 404 to trigger error handling. Some sources have contradicting claims to trigger conflict resolution.

## Anti-patterns directory

`src/research_agents/anti_patterns/` contains deliberately wrong implementations imported only by notebooks. They intentionally violate the architecture rules above -- that is their purpose. Do not "fix" anti-pattern code to match project standards.
