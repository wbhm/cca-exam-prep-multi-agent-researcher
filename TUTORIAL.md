# TUTORIAL: A Reader's Guide to the Notebooks

**Open the article in another tab. Run the notebooks here. This file is your reading order.**

This tutorial walks you through what each notebook does, which section of the published article it pairs with, and which cells to run first. It is the companion to:

- **Article:** [CCA Exam Prep: Mastering the Multi-Agent Research System Scenario](https://pub.towardsai.net/cca-exam-prep-mastering-the-multi-agent-research-system-scenario-aa0c446a5e7d)
- **Code reference:** [`docs/tutorial.md`](docs/tutorial.md) — the module-by-module walkthrough of every Pydantic model, service, tool, and agent.

`TUTORIAL.md` (this file) is the **reading path**. `docs/tutorial.md` is the **reference manual**. Use them together.

```
  [ Article ]          [ TUTORIAL.md ]        [ Notebooks ]          [ docs/tutorial.md ]
  conceptual    ───▶   guided path    ───▶    hands-on      ◀───▶    code reference
  overview             (this file)            (run cells)            (look things up)
```

Read left-to-right for first pass. Once you're in the notebooks, jump to `docs/tutorial.md` whenever you want the module-level detail behind a code pointer.

---

## Three Study Tracks

Pick the one that matches how you're using this repo.

| Track | Time | For whom | What you do |
|---|---|---|---|
| **Exam** | 4–6 hrs | Sitting the CCA Foundations Exam soon | Run every notebook. Do every "Try this." Complete the 15-item study checklist. Take the three walkthrough questions cold. |
| **Concept** | ~90 min | You read the article and want a working model | Skim the article. Open notebooks **02**, **03**, and **04**. In each, run only the three cells labeled "anti-pattern / correct-pattern / `compare_results`". Read the CCA Exam Tip at the bottom. |
| **Reference** | as needed | You know the patterns and want to look up a specific detail | Jump to [`docs/tutorial.md`](docs/tutorial.md). It is indexed by module (`coordinator.py`, `context_builder.py`, `conflict_resolver.py`, etc.) with every model, signature, and design decision. |

The Exam track is what we built this for. The Concept track is the "I have 90 minutes" path — it covers the three anti-patterns that account for the majority of exam distractors.

---

## Before You Start

```bash
poetry install --with notebooks
poetry run pytest                # 180 tests, no API key needed
poetry run jupyter lab           # then open notebooks/
```

No `ANTHROPIC_API_KEY` is required for any notebook — every live-call cell is tagged `skip-execution` and has a mock alongside. Set `ANTHROPIC_API_KEY` only if you want to run the integration cells against the real API.

---

## Notebook-by-Notebook Guide

Each section follows the same shape:

- **What it teaches** — one or two sentences.
- **Article section** — the part of the published article this pairs with.
- **Key cells** — which cells to run first if you're short on time.
- **CCA Exam Tip** — the one this notebook embodies, quoted from the notebook.
- **Try this** — a single exploration that cements the concept.

---

### 📘 [00 — Setup](notebooks/00_setup.ipynb)

**What it teaches.** Verifies your environment, introduces the 60%-of-exam-weight claim, and indexes the rest of the notebooks.

**Article section.** *Why This Scenario Is High Leverage* (the domain-weight table).

**Key cells.** Run all cells — none of them hit an API. The import checks tell you whether `research_agents` is on the path and whether the simulated search index loaded.

**CCA Exam Tip (from 00).** The project covers Agentic Architecture (27%), Tool Design & MCP (18%), and Context Management & Reliability (15%) simultaneously — 60% of exam weight in one scenario. Master this and the rest of the exam gets easier.

**Try this.** `print(len(SEARCH_INDEX))`. Browse `src/research_agents/data/sources.py` and notice that *some sources are written to contradict each other on purpose* — this is what Notebook 06 resolves.

---

### 📘 [01 — Hub-and-Spoke Architecture](notebooks/01_hub_and_spoke.ipynb)

**What it teaches.** One coordinator delegates to specialized subagents. Spokes talk only to the hub, never to each other. Task decomposition produces parallel waves.

**Article section.** *The Hub-and-Spoke Pattern*.

**Key cells.**
- Show each agent's tool count and scoped tool list.
- `sort_tasks_into_waves()` with three tasks — verify `t1` and `t2` land in Wave 0 (parallel) and `t3` lands in Wave 1 (depends on both).

**CCA Exam Tip (from 01).**
> If an answer describes subagents communicating directly with each other or sharing context automatically, that is the distractor. The hub-and-spoke pattern keeps coordination centralized.

**Try this.** Analogy for reinforcement: think of it as a newsroom. The editor (coordinator) assigns stories to reporters (subagents). Reporters don't call each other — they file copy back to the editor, who decides what gets combined into the final story. Now map each element: coordinator → editor, subagents → reporters, `SubTask` → assignment slip, `ResearchReport` → front page. If two reporters are chasing related leads, the editor is the one who spots the overlap — not the reporters themselves.

---

### 📘 [02 — Context Isolation](notebooks/02_context_isolation.ipynb)

**What it teaches.** Subagents receive *only* what the coordinator explicitly passes. The coordinator's message history, system prompt, and other subagents' results are structurally unreachable.

**Article section.** *The Context Isolation Trap* (Question 1 in the walkthrough).

**Key cells.**
- `run_leaky_subagent()` anti-pattern — shows `str(coordinator_messages)` leaking coordinator reasoning and prior-agent output.
- `build_subagent_context(task)` correct pattern — a clean, bounded string.
- `compare_results()` — shows the two contexts side by side.

**CCA Exam Tip (from 02).**
> Any question where a subagent produces results that "should have followed the coordinator's instructions" is testing context isolation. The answer is always that the instructions were in the coordinator's context but never explicitly forwarded.

**Try this.** The canonical exam scenario: coordinator tells user "use APA citations." Web researcher returns MLA citations. Why? Because "use APA citations" was in the coordinator's turn, not in the subagent's `task.context`. Add `"Use APA citation format"` to `task.context` and re-run. Confirm the explicit-context string now contains "APA" while the leaked version also contained "APA" but buried in unrelated coordinator reasoning — that buriedness is exactly the attention-dilution problem.

---

### 📘 [03 — Tool Scoping: 4–5 Tools Per Agent](notebooks/03_tool_scoping.ipynb)

**What it teaches.** 4–5 focused tools per agent. The 18-tool "super agent" is an anti-pattern. Better tool *descriptions* do not fix it — the fix is architectural.

**Article section.** *The Super Agent Anti-Pattern* (Question 2 in the walkthrough).

**Key cells.**
- Print every tool on `SUPER_AGENT_TOOLS` — count exceeds 18.
- Print `ALL_TOOL_SETS` — 5 agents × 4 tools each.
- `compare_results()` — `tools_per_agent: 20` vs `tools_per_agent: 4`.

**CCA Exam Tip (from 03).**
> Answer choices will include "improve tool descriptions" and "add a tool-selection preprocessing step" — both wrong. The correct answer is **decompose into specialized subagents with 4–5 tools each**. The improvement is architectural, not descriptive.

*Why architectural?* The root cause is **attention fragmentation** — an 18-tool menu dilutes the model's focus regardless of how well each tool is described. Sharper descriptions are a band-aid; fewer, scoped tools fix the mechanism.

**Try this.** The show-truck-vs-work-truck analogy: a mechanic arrives at a job site with a show truck that carries *every* tool they own — impressive, but they spend more time searching for the right wrench than turning it. A work truck carries just the 4–5 tools for today's job. Each specialized agent in this project is a work truck. Try it hands-on: add a sixth tool to `WEB_RESEARCHER_TOOLS` in `definitions.py`, re-run the structural tests (`poetry run pytest tests/test_tools.py`), and watch the assertions that enforce the 4-tool bound fail. That is the CCA pattern, enforced in code.

---

### 📘 [04 — Structured Error Handling](notebooks/04_error_handling.ipynb)

**What it teaches.** Tool handlers return `ToolErrorResponse` (`error_type`, `retry_eligible`, `fallback_available`, `source`) on failure — giving the coordinator a decision tree. The anti-pattern returns `{"status":"success","data":null}` and the coordinator cannot tell "no data" from "service failed."

**Article section.** *Silent Failures and the Reliability Domain* (Question 3 in the walkthrough).

**Key cells.**
- `handle_fetch_page_silent(...)` on the timeout URL — returns `success` with `null`.
- `dispatch('web_researcher', 'fetch_page', ...)` on the same URL — returns structured error.
- Same dispatch on the 404 URL — a *different* decision tree (`retry_eligible=False`, `fallback_available=True`).

**CCA Exam Tip (from 04).**
> Distractors: "increase timeout duration" (symptom), "add retry logic" (partial). Correct: **require structured error context from subagents**. The coordinator needs enough information to decide between retry, fallback, or flag-gap — silent failures remove that decision-making ability.

**Try this.** Run `grep -rn 'silent' src/research_agents/anti_patterns/` — notice that every silent failure looks exactly like a successful empty result. Now imagine a 5-step research pipeline where step 2 silently fails. Steps 3–5 proceed on empty data, producing a report that *appears* complete but is missing a critical source. This is how silent failures cascade.

---

### 📘 [05 — Task Decomposition](notebooks/05_task_decomposition.ipynb)

**What it teaches.** `sort_tasks_into_waves()` topologically sorts `SubTask` objects by `depends_on`. Tasks without dependencies run in parallel; dependent tasks run in later waves.

**Article section.** *Task Decomposition: Parallel vs Sequential*.

**Key cells.**
- Four tasks where `web`, `data`, `docs` are independent and `facts` depends on all three — produces 2 waves (one of size 3, one of size 1).
- A fully sequential variant (each depends on the previous) — produces 4 waves of size 1. Compare the two.

**CCA Exam Tip (from 05).**
> If Subtask B needs output from Subtask A → sequential (`depends_on`). If they work from independent inputs → parallel. "Web search" and "document parsing" are the canonical parallel pair. "Fact checking" and "report writing" are always sequential.

**Try this.** Restaurant-kitchen analogy: the appetizer station and the grill work in parallel (independent inputs). Plating waits for both (depends on both). Now try it in code: add a fifth task `report` that `depends_on=['facts']` — the sort should produce 3 waves. Then remove the `depends_on` from `facts` (make it "fact-check whatever is in the query") and watch the wave count collapse. The `depends_on` edge is the only thing creating sequential ordering.

---

### 📘 [06 — Conflict Resolution](notebooks/06_conflict_resolution.ipynb)

**What it teaches.** Three deterministic strategies in priority order: (1) source reliability ranking, (2) majority consensus, (3) flag for human review. Never LLM judgment — always programmatic rules.

**Article section.** *Validation and Conflict Resolution*.

**Key cells.**
- Strategy 1: `.gov` vs blog → reliability wins, confidence > 0.5.
- Strategy 2: three medium-reliability sources vs one medium-reliability source → majority wins.
- Strategy 3: equal reliability + equal count → flagged for human review (confidence 0.3).

**CCA Exam Tip (from 06).**
> The resolution is **deterministic** — same inputs always produce same output. "First result wins" is always the wrong answer. "Let the LLM decide" is also wrong — prompt-based guidance is the distractor; programmatic enforcement is the CCA answer.

*Why deterministic?* Enterprise systems need **predictable, auditable, repeatable** outcomes — a resolution must be reviewable after the fact and reproducible for compliance. LLM judgment can't meet those three requirements; programmatic rules can.

**Try this.** Construct a `ConflictRecord` where both sides have `SourceReliability.HIGH` but one side has 2 sources and the other has 3. Call `resolve_conflict()` — the resolution should be `"majority"`, confidence `3/5 = 0.6`. Now flip it to 2 vs 2 — resolution becomes `"flagged_for_human"`. This is the three-tier fallback at work.

---

### 📘 [07 — MCP Primitives](notebooks/07_mcp_primitives.ipynb)

**What it teaches.** MCP defines three primitives: **Tools** (actions/verbs), **Resources** (data/nouns), **Prompts** (templates/patterns). The most common exam mistake is classifying a Resource as a Tool.

**Article section.** *MCP Primitives: Tools, Resources, Prompts*.

**Key cells.**
- Print `ALL_TOOL_SETS` — every item is an action.
- Print the conceptual resource catalog — every item is read-only data.
- Print the prompt templates — every item is a parameterized pattern.
- The 5-item classification quiz with worked answers.

**CCA Exam Tip (from 07).**
> If a question describes a *source reliability database* → **Resource**, not a Tool. The distractor makes a Resource look like a Tool because both involve "getting information." The difference: Tools have side effects or perform computation; Resources are read-only data.

*Foolproof test:* **if you can't *run* it, it's probably a Resource.** A Tool *performs an action* (e.g., `fetch_page(url)`, `verify_claim(claim)`) — often *using* a Resource. A Resource is the *data or infrastructure the Tool acts upon* (e.g., a database of sources, a schema catalog, a file system). Same information can appear behind either primitive — ask which side of the verb it sits on.

**Try this.** Cover the right-hand column and classify each of these yourself before reading the quiz output: `"fetch_page(url)"`, `"list of source reliability ratings"`, `"APA citation template"`, `"verify_claim(claim)"`, `"database schemas catalog"`. If you classify any of the data items as Tools, re-read Resource definitions in the notebook.

---

### 📘 [08 — End-to-End Integration](notebooks/08_integration.ipynb)

**What it teaches.** All six coordinator steps in one flow: PLAN → SORT → DELEGATE → EVALUATE → RESOLVE → SYNTHESIZE. Uses the `economic_impact` scenario (both a conflict and a gap) and a mock Claude client so the notebook runs without an API key.

**Article section.** *The Three Exam Walkthrough Questions* (this notebook has the end-to-end distractor analysis).

**Key cells.**
- Load `SCENARIOS['economic_impact']` — expected 1 conflict + 1 gap.
- Task decomposition → 2 waves.
- Mock coordinator run → results per task.
- `build_research_report()` → `ResearchReport` with resolved conflicts, declared gaps, adjusted confidence.
- The distractor analysis for all three exam walkthrough questions.

**CCA Exam Tip (from 08).**
> Key models to know: `SubTask` (unit of delegation with explicit context), `ToolErrorResponse` (structured errors), `ConflictRecord` (deterministic resolution metadata), `ResearchReport` (transparent output with gaps and confidence).

**Try this.** Modify the `conflicts` list so *both* sides have only `SourceReliability.HIGH` sources with equal count. Re-run — the report's confidence should drop by 0.05 (the penalty for unresolved conflicts).

---

## The Three Exam Walkthrough Questions

The published article walks through three representative exam questions. Each one maps to specific code and tests in this repository. Use these as cold-read self-checks once you've worked through the notebooks.

### Question 1 — Context Isolation

**Scenario:** A coordinator instructs the user to "use APA citation format." A web-research subagent returns sources formatted in MLA. Why?

**Correct answer.** The APA instruction was in the coordinator's *message history* but was never placed into the subagent's `task.context`. The subagent never saw it.

**Code pointer.** [`notebooks/02_context_isolation.ipynb`](notebooks/02_context_isolation.ipynb) — the `run_leaky_subagent` and `build_subagent_context(task)` cells make this visible side by side. Verified in [`tests/test_context_isolation.py`](tests/test_context_isolation.py).

**Distractors to reject.**
- *"The subagent needs a better system prompt."* No — the issue is missing context, not missing instruction.
- *"Use a larger model for the subagent."* No — a bigger model that also never sees the instruction will make the same mistake, just more fluently.

### Question 2 — Tool Overload

**Scenario:** An agent has 18 tools and selects the wrong one for the task.

**Correct answer.** Decompose into specialized subagents with 4–5 tools each. This is architectural.

**Code pointer.** [`notebooks/03_tool_scoping.ipynb`](notebooks/03_tool_scoping.ipynb) — compares `SUPER_AGENT_TOOLS` (20 tools on one agent) against `ALL_TOOL_SETS` (5 agents × 4 tools). Verified in [`tests/test_anti_patterns.py`](tests/test_anti_patterns.py) (asserts `SUPER_AGENT_TOOLS` count exceeds 18) and [`tests/test_tools.py`](tests/test_tools.py) (asserts each focused set has 4 tools).

**Distractors to reject.**
- *"Improve tool descriptions."* Better descriptions on 18 tools still cause attention fragmentation — this is the canonical trap.
- *"Add a tool-selection preprocessing step."* You've added another agent to hide the problem, not solved it.

### Question 3 — Silent Failure

**Scenario:** A research report is missing a critical source after an upstream API timeout. No error was flagged.

**Correct answer.** Require structured error context from subagents — `ToolErrorResponse` with `error_type`, `retry_eligible`, `fallback_available`, `source`. This gives the coordinator a decision tree.

**Code pointer.** [`notebooks/04_error_handling.ipynb`](notebooks/04_error_handling.ipynb) shows silent vs structured responses on the same timeout URL. Verified in [`tests/test_error_handling.py`](tests/test_error_handling.py).

**Distractors to reject.**
- *"Increase timeout duration."* Symptom fix — the next slow service still fails silently.
- *"Add retry logic."* Partial — retry is one branch of the decision tree, not a substitute for it.

---

## Study Checklist

Tick these off as you work through the notebooks. If you cannot explain an item in one sentence without looking at the code, go back to that notebook.

- [ ] I can describe the hub-and-spoke pattern and name the spokes in this codebase.
- [ ] I can name the function (`build_subagent_context`) that enforces context isolation and say what arguments it *does not* accept.
- [ ] I can state the rule: 4–5 tools per agent, and I can explain why improving tool descriptions does not fix the super-agent anti-pattern.
- [ ] I can list the four fields of `ToolErrorResponse` and explain the decision each one drives.
- [ ] I can explain the difference between a silent failure and an empty-but-legitimate result.
- [ ] I can explain why `depends_on` is the only mechanism that creates sequential ordering.
- [ ] I can trace a task through `sort_tasks_into_waves()` and predict the wave layout.
- [ ] I can name all three conflict-resolution strategies in priority order.
- [ ] I can explain why the conflict resolver is deterministic and not LLM-based.
- [ ] I can state the rule: reports declare gaps explicitly rather than omitting them.
- [ ] I can classify a capability as Tool / Resource / Prompt given a verbal description.
- [ ] I can explain the difference between a Resource and a Tool without using the word "information."
- [ ] I can state the 6-step coordinator flow (PLAN, SORT, DELEGATE, EVALUATE, RESOLVE, SYNTHESIZE).
- [ ] I can identify the three anti-pattern modules in `src/research_agents/anti_patterns/` and explain what each one does wrong.
- [ ] I can name the three domains this scenario draws from and the percentage weight each carries on the exam.

---

## Next Steps

- **Deep code walkthrough.** [`docs/tutorial.md`](docs/tutorial.md) is the module-by-module reference — 16 sections covering every Pydantic model, service, tool, handler, agent, and anti-pattern.
- **The full test suite.** `poetry run pytest` runs 180 tests with no API key required. `tests/test_notebook_execution.py` is the harness that keeps notebooks honest.
- **The broader CCA series.** See [the series index in README.md](README.md#series-context) for the six-article progression. This project is Article 4.
- **Exam preparation.** [Anthropic Academy](https://anthropic.skilljar.com) has 13 free courses aligned to the CCA domains.

If something in a notebook is unclear, the corresponding section of `docs/tutorial.md` has the code-level explanation. If something in `docs/tutorial.md` feels abstract, the corresponding notebook has it running.
