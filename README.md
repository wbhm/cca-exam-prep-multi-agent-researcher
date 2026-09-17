# CCA Exam Prep: Multi-Agent Research System

Hands-on coding example for the [Claude Certified Architect (CCA) Foundations Exam](https://anthropic.skilljar.com) -- the **Multi-Agent Research System** scenario.

This is the scenario that separates strong CCA candidates from average ones. It draws from the three heaviest exam domains simultaneously:

| Domain | Weight | What This Project Covers |
|--------|--------|--------------------------|
| Agentic Architecture & Orchestration | 27% | Hub-and-spoke coordinator, task decomposition, parallel waves |
| Tool Design & MCP Integration | 18% | 4-5 tools per agent, negative-bound descriptions, MCP primitives |
| Context Management & Reliability | 15% | Context isolation, structured errors, conflict resolution |
| **Combined** | **60%** | **Every concept in this project maps to exam questions** |

## How This Maps to the CCA Exam

The CCA exam tests these concepts with specific question patterns. Each notebook demonstrates the correct answer and the most common distractor:

| Notebook | CCA Concept | Correct Answer (demonstrated) | Common Distractor (shown failing) |
|----------|------------|-------------------------------|-----------------------------------|
| 01 Hub-and-Spoke | Architecture | Single coordinator delegates to specialized subagents | Subagents communicate directly with each other |
| 02 Context Isolation | Context passing | Explicit context -- subagent sees ONLY what coordinator sends | Subagents inherit coordinator's conversation history |
| 03 Tool Scoping | Tool count | 4-5 focused tools per agent | 18-tool "super agent" with improved descriptions |
| 04 Error Handling | Reliability | Structured error context (`error_type`, `retry_eligible`) | Silent failure: `{"status":"success","data":null}` |
| 05 Task Decomposition | Orchestration | Parallel + sequential waves based on data dependencies | All tasks run sequentially |
| 06 Conflict Resolution | Synthesis | Reliability ranking -> majority consensus -> human flag | First result wins |
| 07 MCP Primitives | Vocabulary | Tools (verbs), Resources (nouns), Prompts (templates) | Mixing up tools and resources |
| 08 Integration | End-to-end | All patterns combined in a full research query | N/A (capstone) |

## Quick Start

```bash
# 1. Install dependencies
poetry install --with notebooks

# 2. Run the test suite (no API key needed)
poetry run pytest

# 3. Launch notebooks
poetry run jupyter lab
```

No API key is required. No notebook calls the Claude API: every demonstration
replays a scripted transcript (`research_agents.testing.scripted_client`) through
the real agent loop, so every printed number is deterministic. If you create a
`.env` from `.env.example`, notebook 00 loads it and reports whether the key is
set; that only matters if you adapt a cell to use a live client.

## Reading Guides

Two tutorials serve different audiences:

- **[TUTORIAL.md](TUTORIAL.md)** -- *notebook-oriented reading guide*. Start here if you are studying for the exam. Three study tracks (4-6 hrs / 90 min / reference), a per-notebook walkthrough with key cells, the three exam walkthrough questions, and a 15-item study checklist.
- **[docs/tutorial.md](docs/tutorial.md)** -- *code-oriented deep-dive*. Start here if you want to understand every module, model, and design decision. 16 sections organized by package module.

## Deep-Dive Tutorial

For a complete code walkthrough that explains every module, model, and design decision, see **[docs/tutorial.md](docs/tutorial.md)**. The tutorial covers:

- All Pydantic models (`SubTask`, `ResearchReport`, `ConflictRecord`, `ToolErrorResponse`)
- All 4 simulated services and the `ServiceContainer` dependency injection pattern
- Tool definitions with negative-bound descriptions and the dispatch registry
- The agent loop, context builder, and coordinator orchestration
- All 3 anti-patterns with explanations of *why* they fail
- MCP primitives classification (Tools, Resources, Prompts)
- End-to-end data flow through the complete 6-step coordinator pipeline

## Architecture: What the Code Teaches

### The Hub-and-Spoke Pattern (CCA Architecture Domain)

The `coordinator.py` implements a 6-step flow that mirrors the exam's correct answer for multi-agent orchestration:

```
1. PLAN      Decompose query into SubTasks with depends_on fields (done by the caller)
2. SORT      Topological sort into parallel execution waves
3. DELEGATE  Build explicit context -> run_agent_loop with scoped tools
4. EVALUATE  A fact_checker SubTask that depends_on the others cross-references them
5. RESOLVE   Deterministic conflict resolution (not LLM judgment)
6. SYNTHESIZE Compile ResearchReport; gaps are derived from structured tool errors
```

Subagents (spokes) only talk to the coordinator (hub), never to each other.

### Context Isolation (CCA Context Management Domain)

`context_builder.py` is the enforcer. It is the only way `run_coordinator()` builds subagent input:
- **Receives**: `SubTask.instruction`, `SubTask.context` (explicitly selected), predecessor results filtered by `depends_on`
- **Never receives**: coordinator messages, coordinator system prompt, other subagents' results

When the exam asks "the subagent produced results that contradicted the coordinator's instructions" -- the answer is always that the instructions were in the coordinator's context but never explicitly forwarded.

### Tool Scoping: 4-5 Per Agent (CCA Tool Design Domain)

Five agent types, each with exactly 4 focused tools:

| Agent | Tools | Purpose |
|-------|-------|---------|
| Web Researcher | `search_web`, `fetch_page`, `extract_text`, `summarize_source` | Find and process web content |
| Document Analyzer | `parse_document`, `extract_sections`, `identify_claims`, `check_citations` | Analyze document structure |
| Data Extractor | `query_database`, `transform_data`, `validate_schema`, `format_output` | Extract structured data |
| Fact Checker | `verify_claim`, `cross_reference`, `score_reliability`, `flag_conflict` | Verify accuracy |
| Coordinator | `delegate_task`, `collect_results`, `resolve_conflicts`, `compile_report` | Orchestrate and synthesize |

The anti-pattern (`super_agent.py`) combines all 20 tools into one agent. The exam's correct answer is always "decompose into specialized subagents" -- not "improve tool descriptions."

### Structured Error Handling vs Silent Failures (CCA Reliability Domain)

Every tool handler returns a `ToolErrorResponse` on failure (serialized through `tools/_errors.error_response()`) with `error_type`, `source`, `retry_eligible`, `fallback_available`, and `partial_data`. The agent loop logs every tool result and marks errors with `is_error`; `coordinator.collect_gaps()` turns them into the report's `gaps`, which lowers its confidence score. Retry and fallback are decisions left to the caller; the schema is what makes them possible.

The anti-pattern returns `{"status":"success","data":null}` -- making it impossible to distinguish "no data found" from "service failed." The exam answer is always "require structured error context from subagents."

### Deterministic Conflict Resolution

When sources contradict, `conflict_resolver.py` uses three strategies in priority order:
1. **Source reliability ranking**: compare the best tier on each side; `.gov` (3) > news (2) > blog (1). Three blogs never outrank one `.gov`.
2. **Majority consensus**: when the best tiers tie, more sources wins
3. **Flag for human review**: when everything ties

Every `ConflictRecord` says which side won (`winning_side`), so the synthesis step knows not just *how* a conflict was resolved but *which way*.

This is programmatic enforcement -- the CCA principle that code-enforced rules beat prompt-based guidance.

## Project Structure

```
src/research_agents/
  agent/
    coordinator.py          # Hub-and-spoke orchestrator (6-step flow)
    agent_loop.py           # Stop-reason-driven agentic tool-use loop
    context_builder.py      # Enforces context isolation
    subagents.py            # System prompts + tool sets per agent type
    conflict_resolver.py    # Deterministic: reliability, majority, human flag
  testing.py                # Scripted client: replay fixed transcripts through the real loop
  models/
    research.py             # SubTask, ResearchReport, ConflictRecord, etc.
    errors.py               # ToolErrorResponse vs SilentFailureResponse
  services/                 # 4 simulated in-memory services + ServiceContainer + make_default_services()
  tools/
    definitions.py          # 5 tool-set constants (4 tools each)
    handlers.py             # Dispatch registry: DISPATCH[agent_type][tool_name]
    _errors.py              # error_response(): every error is a serialized ToolErrorResponse
    web_researcher.py       # Handler implementations (structured errors)
    document_analyzer.py
    data_extractor.py
    fact_checker.py
  anti_patterns/
    super_agent.py          # 20 tools on one agent, with an unscoped dispatch
    shared_context.py       # Coordinator messages leaked to subagent
    silent_failures.py      # {"status":"success","data":null}
  data/
    sources.py              # Pre-built data with contradictions + errors
    scenarios.py            # 3 research scenarios with expected outcomes
notebooks/                  # 9 teaching notebooks (00-08) with interleaved tutorials
tests/                      # models, services, tools, agent, notebooks, docs
scripts/
  generate_notebooks.py     # Programmatic notebook generation via nbformat
docs/
  tutorial.md               # Complete code walkthrough (all modules + anti-patterns)
```

## Testing

Every test runs without an API key -- services are simulated in-memory and model turns are scripted.

The notebook-test correlation uses a 3-tier safety net:
1. **Structural tests** verify notebooks have correct sections, imports, and metrics, that every `compare_results()` value is measured (no literal booleans), and that the committed notebooks match `scripts/generate_notebooks.py`
2. **Headless execution** runs every untagged cell via `nbformat` + `exec()`
3. **Anti-pattern module tests** verify wrong code is wrong in the right way

## Series Context

This is Article 4 of the CCA Exam Prep series by [Rick Hightower](https://medium.com/@rick-hightower) / [SpillWave](https://spillwave.com):

1. **Complete Guide** -- Exam format, domain weights, study plan
2. **Customer Support Agent** -- Escalation, compliance, tool design ([sibling project](../customer-support/))
3. **Code Generation** -- Context degradation, CLAUDE.md hierarchy, CI/CD
4. **Multi-Agent Research** -- Hub-and-spoke, context isolation, tool scoping (this project)
5. **CI/CD with Claude Code** -- Headless flags, pipeline patterns
6. **Structured Data Extraction** -- JSON schema enforcement, validation loops

## Article-to-Code Mapping

This codebase is the hands-on companion to the article [CCA Exam Prep: Mastering the Multi-Agent Research System Scenario](https://pub.towardsai.net/cca-exam-prep-mastering-the-multi-agent-research-system-scenario-aa0c446a5e7d). Every major section of the article maps to runnable code, a notebook demo, and test coverage:

| Article Section | Code Module | Notebook | Anti-Pattern | Tests |
|---|---|---|---|---|
| Hub-and-Spoke Architecture | `agent/coordinator.py` | `01_hub_and_spoke` | -- | `test_coordinator.py` |
| Context Isolation | `agent/context_builder.py` | `02_context_isolation` | `shared_context.py` | `test_context_isolation.py` |
| The Super Agent Anti-Pattern | `tools/definitions.py`, `agent/subagents.py` | `03_tool_scoping` | `super_agent.py` | `test_anti_patterns.py`, `test_tools.py` |
| Silent Subagent Failures | `models/errors.py`, `tools/handlers.py` | `04_error_handling` | `silent_failures.py` | `test_error_handling.py` |
| Task Decomposition Strategies | `agent/coordinator.py` (`sort_tasks_into_waves`) | `05_task_decomposition` | -- | `test_coordinator.py` |
| Validation and Conflict Resolution | `agent/conflict_resolver.py` | `06_conflict_resolution` | First-result-wins (in the notebook) | `test_conflict_resolver.py` |
| MCP Primitives (Tools, Resources, Prompts) | `tools/definitions.py` | `07_mcp_primitives` | -- | `test_tools.py` |
| End-to-End Integration | All modules | `08_integration` | All 3 anti-patterns | All test files |

### Exam Questions in Code

The article walks through three representative exam questions. Each one maps to specific test assertions in this codebase:

**Question 1 -- Context Isolation** ("subagent returns incorrect citation formatting"):
- Correct answer demonstrated in `test_context_isolation.py`: `build_subagent_context()` returns only explicitly passed content; coordinator messages are structurally unreachable.
- Anti-pattern shown in `shared_context.py`: `run_leaky_subagent()` passes the coordinator's full message history, wasting tokens and polluting attention.

**Question 2 -- Tool Overload** ("agent with 18 tools selects the wrong one"):
- Correct answer demonstrated in `test_tools.py`: each agent type has exactly 4 focused tools with negative-bound descriptions ("does NOT...").
- Anti-pattern shown in `super_agent.py`: `SUPER_AGENT_TOOLS` combines all 20 tools into one list. `test_anti_patterns.py` verifies the count exceeds 18.

**Question 3 -- Silent Failure** ("critical source missing from report after API timeout"):
- Correct answer demonstrated in `test_error_handling.py`: `ToolErrorResponse` includes `error_type`, `retry_eligible`, `fallback_available`, and `source` -- giving the coordinator a decision tree.
- Anti-pattern shown in `silent_failures.py`: returns `{"status":"success","data":null}`, making failures indistinguishable from empty results.

### Discussion Questions and the Notebooks

The article's discussion questions can be explored hands-on using the notebooks:

1. **"Why is hub-and-spoke coordination overhead lower than the super agent attention tax?"** -- Run `03_tool_scoping.ipynb` to see the tool count comparison and one out-of-scope tool call replayed through both routers: the super agent executes it, scoped dispatch refuses it with a structured error. (Selection *accuracy* is a model-behaviour claim the notebook does not measure.)
2. **"What error response fields let you audit past runs for silent failures?"** -- Run `04_error_handling.ipynb` to compare `ToolErrorResponse` fields against the silent `{"status":"success","data":null}` response side-by-side.
3. **"What fields allow the coordinator to retry vs. escalate vs. skip?"** -- The `ToolErrorResponse` model in `models/errors.py` has exactly these fields: `retry_eligible` (retry timeouts), `error_type` (escalate parse failures), `fallback_available` (skip permanently unavailable sources).

## Recommended Study Resources

- [Anthropic Academy](https://anthropic.skilljar.com) -- 13 free courses
- [Claude Agent SDK Docs](https://docs.anthropic.com/) -- Agent patterns
- [MCP Documentation](https://modelcontextprotocol.io/) -- Tool/Resource/Prompt primitives
