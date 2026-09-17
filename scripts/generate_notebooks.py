"""Generate all teaching notebooks programmatically via nbformat.

This script is the source of truth for ``notebooks/*.ipynb``. Edit the
``gen_NN`` functions here, re-run the script, and commit the regenerated
notebooks. ``tests/test_notebooks.py::test_notebooks_match_generator`` fails
if a committed notebook drifts from what this script produces.

Every code cell is executed headlessly by ``tests/test_notebook_execution.py``
except cells tagged ``skip-execution``. No notebook calls the Claude API:
demonstrations replay scripted transcripts (``research_agents.testing``)
through the real agent loop so every printed number is deterministic.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import nbformat

NOTEBOOKS_DIR = Path(__file__).parent.parent / "notebooks"

PATH_SHIM = """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path('..').resolve()))
    sys.path.insert(0, str(Path('.').resolve()))
"""


def _clean(text: str) -> str:
    return textwrap.dedent(text).strip("\n")


def _md(text: str) -> nbformat.NotebookNode:
    return nbformat.v4.new_markdown_cell(_clean(text))


def _code(source: str, skip: bool = False) -> nbformat.NotebookNode:
    cell = nbformat.v4.new_code_cell(_clean(source))
    if skip:
        cell.metadata["tags"] = ["skip-execution"]
    return cell


def _make_nb(cells: list) -> nbformat.NotebookNode:
    nb = nbformat.v4.new_notebook()
    nb.cells = cells
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    return nb


def build_all() -> dict[str, nbformat.NotebookNode]:
    """Return every notebook keyed by file name (used by the sync test)."""
    return {
        "00_setup.ipynb": gen_00(),
        "01_hub_and_spoke.ipynb": gen_01(),
        "02_context_isolation.ipynb": gen_02(),
        "03_tool_scoping.ipynb": gen_03(),
        "04_error_handling.ipynb": gen_04(),
        "05_task_decomposition.ipynb": gen_05(),
        "06_conflict_resolution.ipynb": gen_06(),
        "07_mcp_primitives.ipynb": gen_07(),
        "08_integration.ipynb": gen_08(),
    }


# ---- Notebook 00: Setup ----

def gen_00() -> nbformat.NotebookNode:
    return _make_nb([
        _md("""
            # 00 --- Setup

            Verify your environment is ready for the CCA Multi-Agent Research System notebooks.

            ## Why This Scenario Is 60% of Exam Weight

            > Before you run the imports: understand why this particular scenario matters
            disproportionately. Most CCA scenarios draw from one or two domains.
            Multi-agent research draws from the three heaviest simultaneously.

            | Domain | Weight | What It Tests Here |
            |--------|--------|--------------------|
            | Agentic Architecture & Orchestration | **27%** | Hub-and-spoke, task decomposition, parallel waves |
            | Tool Design & MCP Integration | **18%** | 4-5 tools per agent, negative bounds, MCP primitives |
            | Context Management & Reliability | **15%** | Context isolation, structured errors, conflict resolution |
            | **Combined coverage** | **60%** | Every exam concept in this scenario maps to a question pattern |

            This means studying this one scenario deeply teaches you more than studying
            three separate scenarios that each cover one domain. The article this
            companion pairs with calls this scenario "the one that separates strong
            candidates from average ones" -- because the same candidate who can navigate
            multi-agent research almost always handles the other scenarios too.

            Each notebook demonstrates a CCA anti-pattern side-by-side with the correct
            architectural pattern, using runnable code you can experiment with.
        """),
        _md("""
            ## Project Architecture at a Glance

            The codebase has two layers:

            1. **The Python package** (`src/research_agents/`) -- production implementation
            with correct patterns only
            2. **Anti-patterns** (`src/research_agents/anti_patterns/`) -- deliberately wrong
            implementations imported only by notebooks and their tests

            The coordinator follows a **6-step orchestration flow**:

            ```
            Research query
              -> 1. PLAN:      Decompose into SubTasks with depends_on fields (done by the caller)
              -> 2. SORT:      Topological sort into parallel execution waves
              -> 3. DELEGATE:  Build explicit context -> run_agent_loop with scoped tools
              -> 4. EVALUATE:  A fact_checker SubTask cross-references the others' results
              -> 5. RESOLVE:   Deterministic conflict resolution (not LLM judgment)
              -> 6. SYNTHESIZE: Compile ResearchReport; gaps come from structured tool errors
            ```

            ### How the demonstrations work

            **No notebook in this series calls the Claude API.** Every demonstration
            replays a *scripted transcript* -- the responses a model would give --
            through the real `run_agent_loop()`, the real tool dispatch, and the real
            simulated services. That makes every number you see deterministic, and it
            lets one transcript be replayed through an anti-pattern and the correct
            pattern so only the thing being taught changes.
        """),
        _code("import sys\nprint(f'Python {sys.version}')"),
        _code("import research_agents\nprint(f'research_agents v{research_agents.__version__}')"),
        _code("""
            from research_agents.services.container import make_default_services
            from research_agents.data.sources import SEARCH_INDEX

            services = make_default_services()
            print(f'Search index has {len(SEARCH_INDEX)} keyword groups')
            print(f'Knowledge base has {services.knowledge_base.fact_count} verified facts')
            print(f'Database tables: {services.database.table_names}')
        """),
        _code("""
            # Optional: load .env and check for an API key.
            # No notebook in this series calls the Claude API -- every demonstration
            # replays a scripted transcript through the real agent loop. The key is only
            # needed if you adapt a cell to use a live anthropic.Anthropic() client.
            import os
            from dotenv import find_dotenv, load_dotenv

            loaded = load_dotenv(find_dotenv(usecwd=True))
            key = os.environ.get('ANTHROPIC_API_KEY', '')
            print(f'.env found and loaded: {loaded}')
            if key and key != 'your-api-key-here':
                print('[OK] ANTHROPIC_API_KEY is set (not required for these notebooks)')
            else:
                print('[INFO] ANTHROPIC_API_KEY not set -- fine, no notebook calls the API')
        """, skip=True),
        _md("""
            ## Setup Complete

            If all cells above ran without errors, you're ready to proceed to Notebook 01.

            ### Notebook Index

            | # | Topic | CCA Domain |
            |---|-------|------------|
            | 01 | Hub-and-Spoke Architecture | Agentic Architecture (27%) |
            | 02 | Context Isolation | Context Management (15%) |
            | 03 | Tool Scoping | Tool Design & MCP (18%) |
            | 04 | Structured Error Handling | Reliability (15%) |
            | 05 | Task Decomposition | Agentic Architecture (27%) |
            | 06 | Conflict Resolution | Reliability (15%) |
            | 07 | MCP Primitives | Tool Design & MCP (18%) |
            | 08 | Integration | All three domains (60%) |
        """),
    ])


# ---- Notebook 01: Hub-and-Spoke Architecture ----

def gen_01() -> nbformat.NotebookNode:
    return _make_nb([
        _md("""
            # 01 --- Hub-and-Spoke Architecture

            **CCA Pattern**: The coordinator sits at the hub. Specialized subagents are the
            spokes. Spokes talk only to the hub, never to each other.

            This notebook shows the data structures that make that shape, and shows
            *where in the code* a sideways call is refused.
        """),
        _code(PATH_SHIM),
        _code("""
            import dataclasses
            import inspect
            import json

            from research_agents.models.research import SubTask
            from research_agents.agent.coordinator import sort_tasks_into_waves
            from research_agents.agent.context_builder import build_subagent_context
            from research_agents.agent.subagents import SUBAGENT_CONFIGS
            from research_agents.services.container import ServiceContainer, make_default_services
            from research_agents.tools.handlers import dispatch
            from research_agents.tools.web_researcher import handle_search_web

            services = make_default_services()
        """),
        _md("""
            ## Understanding the Key Data Structures

            ### SubTask -- The Unit of Delegation

            The `SubTask` model (from `models/research.py`) is the data structure the coordinator
            uses to delegate work. Each field maps to a CCA concept:

            ```python
            class SubTask(BaseModel):
                task_id: str           # Unique identifier for dependency tracking
                agent_type: str        # Which specialized agent handles this
                instruction: str       # What to do (the "task")
                context: str           # ONLY what the coordinator chose to pass
                depends_on: list[str] = Field(default_factory=list)  # task_ids that must complete first
            ```

            The critical field is `context`. It contains **only** what the coordinator explicitly
            selected -- not the coordinator's full conversation history. This is context isolation
            in data form. We'll explore this deeply in Notebook 02.

            ### SubagentConfig -- System Prompt + Scoped Tools

            Each agent type has a frozen configuration in `agent/subagents.py`:

            ```python
            @dataclass(frozen=True)
            class SubagentConfig:
                system_prompt: str   # Agent-specific instructions
                tools: list[dict]    # 4 scoped tools (never the full set)
            ```

            The `frozen=True` means configs are immutable after creation. A web researcher
            always gets the same 4 tools -- the coordinator cannot accidentally give it
            fact-checking tools at runtime.
        """),
        _md("""
            ## The Newsroom Analogy

            Think of the architecture as a newsroom:

            - **Coordinator = Editor.** Assigns stories, decides the front page, resolves
            disagreements between reporters.
            - **Subagents = Specialist reporters.** One covers business, one covers science,
            one fact-checks. Each has their own beat, their own contacts, their own tools.
            - **`SubTask` = Assignment slip.** Tells a reporter what to write, what angle
            the editor wants, and what background the reporter needs to get started.
            - **`ResearchReport` = The published story.** Combines all filed copy with
            editorial judgment about what's verified and what's still open.

            Reporters do not call each other mid-assignment. If the business reporter
            needs something from the science reporter, the editor brokers it. This is
            the hub-and-spoke shape -- and it is exactly why subagent-to-subagent
            communication is the wrong answer on the CCA exam.
        """),
        _md("""
            ## Anti-Pattern: Subagent-to-Subagent Communication

            The most common distractor on the exam lets subagents talk directly.
            It looks efficient but it breaks the coordination contract. Pseudocode:

            ```python
            # WRONG: subagent calls another subagent directly
            def run_web_researcher(task):
                sources = search_web(task.query)
                # Reach out sideways to the fact checker
                verified = fact_checker_agent.verify(sources)   # no!
                return verified
            ```

            What breaks:

            - **No single point of coordination.** The editor no longer knows what was verified.
            - **Context leakage.** The fact checker inherits the web researcher's task context
            (violating the isolation rule from Notebook 02).
            - **Unpredictable ordering.** `sort_tasks_into_waves()` loses its meaning --
            any subagent can trigger any other at any time.
            - **No conflict resolution.** When the web researcher and fact checker disagree,
            there is no hub to reconcile them (that is Notebook 06).

            ### Where the code refuses a sideways call

            The pseudocode above cannot be written against this package, and the next
            cell shows why by inspecting three signatures. A tool handler receives its
            input and a `ServiceContainer` -- there is no client and no other agent in
            reach. The container holds data services only. And the one function that
            builds a subagent's input takes a `SubTask`, never another agent's session.
        """),
        _code("""
            print('What a tool handler receives: ', inspect.signature(handle_search_web))
            print('What ServiceContainer holds:  ', [f.name for f in dataclasses.fields(ServiceContainer)])
            print('What builds subagent input:   ', inspect.signature(build_subagent_context))
        """),
        _md("""
            The closest a web researcher could come to "calling the fact checker" is
            asking dispatch for a fact-checking tool. Dispatch is scoped per agent
            (Notebook 03), so that request is refused with a structured error:
        """),
        _code("""
            sideways = json.loads(dispatch('web_researcher', 'verify_claim', {'claim': 'x'}, services))
            print(f"{sideways['status']}: {sideways['message']}")
        """),
        _md("## Correct Pattern: Specialized Subagents\n\nEach agent has its own system prompt and 4 scoped tools."),
        _code("""
            # Show each agent's tool count and tool names
            for agent_type, config in SUBAGENT_CONFIGS.items():
                tool_names = [t['name'] for t in config.tools]
                print(f'{agent_type}: {len(config.tools)} tools')
                print(f'  Tools: {", ".join(tool_names)}')
                print(f'  Prompt preview: {config.system_prompt[:80].strip()}...')
                print()
        """),
        _md("""
            ### How the Coordinator Delegates

            The caller decomposes a query into `SubTask` objects (step 1; this package has
            no decomposition code of its own), then `sort_tasks_into_waves()` in
            `coordinator.py` topologically sorts them into **waves** based on `depends_on`:

            - **Wave 0**: Tasks with no dependencies (can run in parallel)
            - **Wave 1**: Tasks depending on wave-0 results (sequential)
            - **Wave N**: Tasks depending on wave-(N-1) results

            Let's see it in action:
        """),
        _code("""
            # Demonstrate task decomposition into parallel waves
            tasks = [
                SubTask(task_id='t1', agent_type='web_researcher',
                    instruction='Search for renewable energy data',
                    context='Focus on 2024'),
                SubTask(task_id='t2', agent_type='data_extractor',
                    instruction='Query capacity statistics',
                    context='renewable_capacity table'),
                SubTask(task_id='t3', agent_type='fact_checker',
                    instruction='Verify claims',
                    context='', depends_on=['t1', 't2']),
            ]
            waves = sort_tasks_into_waves(tasks)
            for i, wave in enumerate(waves):
                task_ids = [t.task_id for t in wave]
                print(f'Wave {i}: {task_ids} ({", ".join(t.agent_type for t in wave)})')
        """),
        _md("""
            Notice that `t1` (web_researcher) and `t2` (data_extractor) are in Wave 0 because
            they have no dependencies -- they can run in parallel. `t3` (fact_checker) depends
            on both, so it goes in Wave 1.

            ### The ServiceContainer -- Dependency Injection

            All tool handlers receive a `ServiceContainer` rather than importing services directly:

            ```python
            @dataclass(frozen=True)
            class ServiceContainer:
                web_search: WebSearchService
                document_store: DocumentStore
                database: DatabaseService
                knowledge_base: KnowledgeBase
            ```

            The `frozen=True` makes the container immutable. This is dependency injection --
            if you later replace `WebSearchService` with a real API client, only the container
            construction changes. Tool handlers are untouched.
        """),
        _md("""
            ### Comparison

            The channel counts below are derived from the topology (every pair of
            agents in a peer mesh vs. one channel per spoke in a hub-and-spoke). The
            last row is measured: it replays the sideways `verify_claim` call through
            the unscoped super-agent router from Notebook 03 and through the scoped
            `dispatch`.
        """),
        _code("""
            from helpers import compare_results
            from research_agents.anti_patterns.super_agent import super_agent_dispatch

            n = len(SUBAGENT_CONFIGS)
            mesh_call = json.loads(super_agent_dispatch('web_researcher', 'verify_claim', {'claim': 'x'}, services))

            compare_results(
                {'subagents': n, 'communication_channels': n * (n - 1) // 2, 'coordination_points': n,
                 'sideways_call_refused': mesh_call['status'] == 'error'},
                {'subagents': n, 'communication_channels': n, 'coordination_points': 1,
                 'sideways_call_refused': sideways['status'] == 'error'},
            )
        """),
        _md("""
            ## CCA Exam Tip

            > When a CCA exam question asks about the correct architecture for a multi-agent system:
            > - **Look for** the option with a single coordinator delegating to specialized subagents
            > - **If an answer** describes subagents communicating directly with each other
            or sharing context automatically, that is the distractor
            > - The hub-and-spoke pattern keeps coordination centralized
            > - Each spoke (subagent) has its own system prompt, scoped tools, and
            receives only explicit context
        """),
    ])


# ---- Notebook 02: Context Isolation ----

def gen_02() -> nbformat.NotebookNode:
    return _make_nb([
        _md("""
            # 02 --- Context Isolation

            **CCA Pattern**: Subagents do NOT inherit coordinator context. Each starts blank
            -- it receives ONLY what was explicitly passed.

            This is the concept that trips up more candidates than any other. This
            notebook runs three subagents through the real agent loop with a recording
            client and inspects **what each one was actually sent**.
        """),
        _code(PATH_SHIM),
        _code("""
            from research_agents.models.research import SubTask
            from research_agents.agent.context_builder import build_subagent_context
            from research_agents.agent.agent_loop import AgentResult, run_agent_loop
            from research_agents.agent.subagents import SUBAGENT_CONFIGS
            from research_agents.services.container import make_default_services
            from research_agents.testing import scripted_client, text_turn

            services = make_default_services()
            web_config = SUBAGENT_CONFIGS['web_researcher']
        """),
        _md("""
            ## How Context Isolation Works

            The `build_subagent_context()` function in `agent/context_builder.py` is the
            only way `run_coordinator()` creates subagent input. It builds a plain string
            from three sources:

            1. **`task.instruction`** -- what to do (always present)
            2. **`task.context`** -- explicitly selected facts from the coordinator
            3. **Predecessor results** -- filtered to only `task.depends_on` task IDs

            What the subagent does **NOT** receive:
            - The coordinator's message history
            - The coordinator's system prompt
            - Other subagents' results (unless listed in `depends_on`)
            - The original research query (unless the coordinator chose to include it)

            This is **structural isolation** -- the function signature makes it impossible
            to accidentally leak coordinator state:

            ```python
            def build_subagent_context(
                task: SubTask,
                predecessor_results: dict[str, AgentResult] | None = None,
            ) -> str:
            ```

            The coordinator's `messages` list is not even a parameter. You cannot pass it.
            (`run_agent_loop()` itself accepts any string as the user message -- that is
            the door the anti-pattern below walks through.)
        """),
        _md("""
            ## Worked Example: Why Subagents Return MLA When Told to Use APA

            This is the canonical CCA exam scenario for context isolation.

            1. A user asks the coordinator: *"Research renewable energy adoption. Use
            APA citation format for all sources."*
            2. The coordinator reasons: "I'll decompose this into web research,
            document analysis, and fact checking."
            3. The coordinator creates `SubTask` objects. Each `instruction` says
            "Search for renewable energy data" (or similar). **The APA requirement
            never makes it into any `SubTask.context`.**
            4. The web researcher runs, does a fine job finding sources, and returns
            citations formatted however it defaults -- MLA, say.
            5. The user sees the final report, notices the citations are wrong, and
            reports it as a bug.

            **Why the exam calls this the most-missed pattern:** it looks like the
            subagent disobeyed the coordinator. It didn't. It never received the
            instruction. The APA requirement was in the coordinator's turn-1 message,
            which the subagent structurally cannot see.

            **The fix is explicit forwarding.** Anything that applies to a subagent
            (citation format, tone, date range, output schema) must be copied into its
            `SubTask.context`. No inheritance. No magic.

            The tempting *wrong* fix is to hand the subagent the whole coordinator
            conversation "so it can't miss anything". That is the anti-pattern, and the
            cells below measure what it actually sends.

            ### The coordinator history used in every cell below

            Three messages: the user's request (with the APA rule), the coordinator's
            own reasoning, and a tool result that came back from a *different*
            subagent. What a subagent should and should not see is now concrete.
        """),
        _code("""
            coordinator_messages = [
                {'role': 'user', 'content': 'Research renewable energy adoption globally. '
                                            'Use APA citation format for all sources.'},
                {'role': 'assistant', 'content': 'I will decompose this into web research, '
                                                 'document analysis, and fact checking.'},
                {'role': 'user', 'content': '[tool_result from document_analyzer t2] '
                                            'IEA report: solar capacity reached 1580 GW in 2024.'},
            ]

            APA = 'APA citation format'          # the instruction the subagent must see
            REASONING = 'I will decompose'       # coordinator's private reasoning
            OTHER_AGENT = '1580 GW'              # another subagent's result

            def sent_to_subagent(client) -> str:
                \"\"\"The user message the subagent actually received on its first turn.\"\"\"
                return client.calls[0]['messages'][0]['content']
        """),
        _md("""
            ## Anti-Pattern: Shared Context

            `run_leaky_subagent()` in `anti_patterns/shared_context.py` passes the
            coordinator's full message history to the subagent. We run it through the
            real loop with a recording client and read back what was sent.
        """),
        _code("""
            from research_agents.anti_patterns.shared_context import run_leaky_subagent

            leaky_client = scripted_client([text_turn('Found 3 sources.')])
            run_leaky_subagent(leaky_client, services, coordinator_messages, 'web_researcher')

            leaked_context = sent_to_subagent(leaky_client)
            print(f'Leaked context length: {len(leaked_context)} chars')
            print(f'Has citation instruction:    {APA in leaked_context}')
            print(f'Has coordinator reasoning:   {REASONING in leaked_context}')
            print(f"Has another agent's result:  {OTHER_AGENT in leaked_context}")
            print()
            print(leaked_context[:160] + '...')
        """),
        _md("""
            ### Why This Fails

            The subagent did get the APA rule -- along with everything else. The cell
            shows three problems in the one string it received:

            - **Context pollution**: the web researcher sees the coordinator's private
            planning ("I will decompose...") and a document analyzer's tool result. Neither
            is its job, and both compete for attention with its actual task.
            - **No isolation**: whatever any other subagent produced is now visible to
            this one, so a mistake upstream propagates everywhere.
            - **Wrong format**: `str(coordinator_messages)` is a Python `repr` of a list of
            dicts, not a task. The subagent has to parse role markers to find its
            instruction.

            Token waste scales with conversation length: a three-message history is short
            here, but a real coordinator history is thousands of tokens the subagent
            re-reads on every turn.
        """),
        _md("""
            ## Correct Pattern: Explicit Context Passing

            The context builder passes ONLY what the coordinator deliberately selects.
            That cuts both ways, so we run it twice.

            ### Case 1 -- the exam's bug: the coordinator forgot to forward APA
        """),
        _code("""
            forgot_task = SubTask(
                task_id='t1',
                agent_type='web_researcher',
                instruction='Search for renewable energy adoption statistics',
                context='Focus on 2024 data from government and peer-reviewed sources.',
            )
            forgot_client = scripted_client([text_turn('Found 3 sources.')])
            run_agent_loop(forgot_client, services, build_subagent_context(forgot_task),
                           web_config.system_prompt, web_config.tools, 'web_researcher')

            forgot_context = sent_to_subagent(forgot_client)
            print(forgot_context)
            print()
            print(f'Has citation instruction: {APA in forgot_context}')
        """),
        _md("""
            The subagent received a clean task and **no citation rule**. Whatever format it
            returns is not disobedience; the rule was never in its input. This is the
            exact failure the exam describes -- and note that nothing in the code raised
            an error, because from the code's point of view the coordinator did exactly
            what it asked.

            ### Case 2 -- the fix: forward the rule in `SubTask.context`
        """),
        _code("""
            task = SubTask(
                task_id='t1',
                agent_type='web_researcher',
                instruction='Search for renewable energy adoption statistics',
                context='Focus on 2024 data from government and peer-reviewed sources. '
                        'Use APA citation format.',
            )
            explicit_client = scripted_client([text_turn('Found 3 sources.')])
            run_agent_loop(explicit_client, services, build_subagent_context(task),
                           web_config.system_prompt, web_config.tools, 'web_researcher')

            explicit_context = sent_to_subagent(explicit_client)
            print(f'Explicit context length: {len(explicit_context)} chars')
            print(f'Has citation instruction:    {APA in explicit_context}')
            print(f'Has coordinator reasoning:   {REASONING in explicit_context}')
            print(f"Has another agent's result:  {OTHER_AGENT in explicit_context}")
            print()
            print(explicit_context)
        """),
        _md("""
            ### Predecessor Results: The `depends_on` Filter

            When a task depends on earlier tasks, the context builder includes only those
            specific results -- not all prior results:
        """),
        _code("""
            # Simulate predecessor results from Wave 0
            prior_results = {
                't1': AgentResult(content='Found 4 sources on renewable energy.'),
                't2': AgentResult(content='Database shows 1580 GW solar capacity in 2024.'),
                't3': AgentResult(content='Document analysis of IEA report complete.'),
            }

            # Fact checker depends on t1 and t2 only -- NOT t3
            fact_check_task = SubTask(
                task_id='t4',
                agent_type='fact_checker',
                instruction='Verify renewable energy claims',
                context='Cross-reference web and database findings',
                depends_on=['t1', 't2'],  # Only these results are passed
            )

            context_with_deps = build_subagent_context(fact_check_task, prior_results)
            print(context_with_deps)
            print()
            print(f'Contains t1 result: {"Found 4 sources" in context_with_deps}')
            print(f'Contains t2 result: {"1580 GW" in context_with_deps}')
            print(f'Contains t3 result: {"IEA report" in context_with_deps}')
        """),
        _md("""
            ### Comparison

            Every value below is read from what the recording client captured, i.e. the
            user message each subagent was actually sent. Boolean rows are phrased as
            properties the correct pattern should have, so `FIXED` means the fix is
            present.
        """),
        _code("""
            from helpers import compare_results

            print('Anti-pattern (leaky) vs. correct (explicit, APA forwarded):')
            compare_results(
                {'context_length': len(leaked_context),
                 'has_citation_instruction': APA in leaked_context,
                 'free_of_coordinator_reasoning': REASONING not in leaked_context,
                 'free_of_other_agent_results': OTHER_AGENT not in leaked_context,
                 'sent_as': 'repr(messages)'},
                {'context_length': len(explicit_context),
                 'has_citation_instruction': APA in explicit_context,
                 'free_of_coordinator_reasoning': REASONING not in explicit_context,
                 'free_of_other_agent_results': OTHER_AGENT not in explicit_context,
                 'sent_as': 'task string'},
            )
            print()
            print("The exam's bug (rule not forwarded) vs. the fix (rule forwarded):")
            compare_results(
                {'has_citation_instruction': APA in forgot_context},
                {'has_citation_instruction': APA in explicit_context},
            )
        """),
        _md("""
            ## CCA Exam Tip

            > Any question where a subagent produces results that 'should have followed the
            coordinator's instructions' is testing context isolation.
            > - The answer is always that the instructions were in the coordinator's context
            but never explicitly forwarded
            > - Subagents do not inherit. Subagents receive only what you explicitly send.
            > - The `build_subagent_context()` pattern enforces this structurally --
            the coordinator's messages are never a function parameter
            > - "Send the whole history" is the distractor: it forwards the rule *and*
            everything else, as the leaky run above shows

            What this notebook does **not** test: whether the model *obeys* an APA rule
            once it sees one. That is model behaviour. What it measures is what the model
            can see, which is the part architecture controls.
        """),
    ])


# ---- Notebook 03: Tool Scoping ----

def gen_03() -> nbformat.NotebookNode:
    return _make_nb([
        _md("""
            # 03 --- Tool Scoping: 4-5 Tools Per Agent

            **CCA Pattern**: Each agent gets 4-5 focused tools. The super agent anti-pattern
            (18 or more tools on one agent; ours has 20) causes tool selection degradation.

            The exam's official guidance is specific: **keep 4-5 tools per agent**.
            This is the exam-correct answer.
        """),
        _code(PATH_SHIM),
        _code("""
            import json

            from research_agents.tools.definitions import ALL_TOOL_SETS
            from research_agents.tools.handlers import dispatch
            from research_agents.anti_patterns.super_agent import (
                SUPER_AGENT_TOOLS, get_super_agent_tool_count, super_agent_dispatch,
            )
            from research_agents.agent.agent_loop import run_agent_loop
            from research_agents.agent.subagents import SUBAGENT_CONFIGS
            from research_agents.services.container import make_default_services
            from research_agents.testing import scripted_client, text_turn, tool_turn

            services = make_default_services()
        """),
        _md("""
            ## How Tool Definitions Work

            Tool definitions live in `tools/definitions.py`. Each agent type has a constant
            list of tool dicts, for example `WEB_RESEARCHER_TOOLS`.

            Each tool dict follows the Claude API format:

            ```python
            {
                "name": "search_web",
                "description": (
                    "Search the public web for information matching a query. "
                    "Returns URLs, titles, and snippets. "
                    "Does NOT fetch full page content (use fetch_page for that). "
                    "Does NOT search internal documents or databases."
                ),
                "input_schema": { ... }
            }
            ```

            ### Negative-Bound Descriptions

            Every tool description includes **"Does NOT..."** clauses. This is the CCA
            negative-bound pattern -- it tells Claude what a tool *cannot* do, preventing
            misrouting. Without these, Claude might call `search_web` when it needs
            `parse_document`, because both involve finding information.

            ### The Dispatch Registry

            Tool handlers are dispatched via a nested dict in `tools/handlers.py`:

            ```python
            DISPATCH: dict[str, dict[str, Handler]] = {
                "web_researcher": {
                    "search_web": handle_search_web,
                    "fetch_page": handle_fetch_page,
                    ...
                },
                ...
            }
            ```

            The key insight: dispatch is keyed by agent type *then* tool name. A tool is
            only reachable through the agent that owns it, and an out-of-scope call gets a
            structured error, not a handler. Tools are isolated per agent at the dispatch
            level, which is enforcement in code rather than a request in a prompt.
        """),
        _md("## Anti-Pattern: Super Agent with 18+ Tools"),
        _code("""
            # The super agent has ALL tools combined
            print(f'Super agent tool count: {get_super_agent_tool_count()}')
            print()
            print('All tools on one agent:')
            for i, tool in enumerate(SUPER_AGENT_TOOLS, 1):
                print(f'  {i:2d}. {tool["name"]:<25s} {tool["description"][:60]}...')
        """),
        _md("""
            ### Why 18+ Tools Fails

            When an agent has 18 or more tools (20 here):
            - A significant portion of attention goes to evaluating tool descriptions
            instead of the actual task
            - Similar tools create ambiguity (e.g., `search_web` vs `cross_reference` --
            both find information)
            - **Better descriptions don't fix the structural problem** -- this is a
            key exam distractor

            Those are claims about model behaviour, and this notebook cannot measure
            them without a live model. What it *can* show is the structural half: with
            one giant tool list there is nothing in the code that stops a wrong choice
            from executing. The replay below does exactly that.
        """),
        _md("""
            ## The Show Truck vs. Work Truck Analogy

            A useful mental model for the exam: imagine a mechanic arriving at a job site.

            - **The show truck** is magnificent. It carries *every tool the mechanic owns* --
            drawer after drawer of sockets, a dozen types of wrench, diagnostic computers, a
            lift and a press. Impressive. Also: every time the mechanic needs a 10mm
            socket, they search through every drawer. Every minute spent searching is a
            minute not spent working. The show truck looks capable but is *operationally*
            slow because selection cost dominates work cost.

            - **The work truck** carries exactly the 4-5 tools for today's job. The
            mechanic reaches without looking. No selection overhead. If tomorrow's job
            needs different tools, they swap the loadout -- they don't bolt on more
            drawers.

            Every specialized agent in this project is a work truck. The `super_agent`
            anti-pattern is a show truck. The CCA exam's correct answer is always
            "give the mechanic the right work truck" -- not "improve the labels on
            the show truck's drawers."

            Concretely in this codebase: `WEB_RESEARCHER_TOOLS` is the web researcher's
            work truck. `DOCUMENT_ANALYZER_TOOLS` is the document analyzer's. Each set
            has exactly 4 tools. When the coordinator dispatches a task, it hands the
            *right* work truck to the *right* mechanic. That handoff is structural,
            not suggestive -- the dispatch registry in `tools/handlers.py` is nested by
            agent type and then tool name, so a tool that is not on this agent's truck
            cannot be reached from it.
        """),
        _md("## Correct Pattern: Focused Tool Sets"),
        _code("""
            # Each subagent has 4 focused tools. The coordinator has its own set of 4 too.
            print('Focused tool sets:')
            for agent_type, tools in ALL_TOOL_SETS.items():
                tool_names = [t['name'] for t in tools]
                role = 'subagent' if agent_type in SUBAGENT_CONFIGS else 'hub'
                print(f'  {agent_type:<20s} ({len(tools)} tools, {role}): {", ".join(tool_names)}')
        """),
        _md("""
            ### What scoping enforces: replay one transcript through both routers

            The scripted transcript below is a web researcher that decides to call
            `query_database` -- a data extractor's tool. The same transcript runs through
            the real loop twice. The only difference is the router: the super agent's flat
            map, or the scoped `dispatch`.
        """),
        _code("""
            transcript = [
                tool_turn('query_database', {'table': 'remote_work_stats'}),
                text_turn('Done.'),
            ]
            web_config = SUBAGENT_CONFIGS['web_researcher']

            def replay(dispatch_fn) -> dict:
                client = scripted_client(list(transcript))
                result = run_agent_loop(client, services, 'Find remote work statistics',
                                        web_config.system_prompt, web_config.tools,
                                        'web_researcher', dispatch_fn=dispatch_fn)
                return json.loads(result.tool_results[0]['result'])

            super_result = replay(super_agent_dispatch)
            scoped_result = replay(dispatch)

            print(f"Super agent:  {super_result['status']} -- "
                  f"{len(super_result['data']['rows'])} rows returned from the database")
            print(f"Scoped agent: {scoped_result['status']} -- {scoped_result['message']}")
        """),
        _code("""
            from helpers import compare_results

            compare_results(
                {'max_tools_per_agent': get_super_agent_tool_count(),
                 'subagents': 1,
                 'out_of_scope_call_blocked': super_result['status'] == 'error'},
                {'max_tools_per_agent': max(len(c.tools) for c in SUBAGENT_CONFIGS.values()),
                 'subagents': len(SUBAGENT_CONFIGS),
                 'out_of_scope_call_blocked': scoped_result['status'] == 'error'},
            )
        """),
        _md("""
            ## CCA Exam Tip

            > The super agent question is one of the most reliable on the CCA exam.
            > Answer choices will include:
            > - 'improve tool descriptions' -- WRONG
            > - 'add a tool-selection preprocessing step' -- WRONG
            > - **'decompose into specialized subagents with 4-5 tools each' -- CORRECT**
            > The improvement is architectural, not descriptive.

            *Why architectural?* The root cause is **attention fragmentation** --
            an 18-tool menu dilutes the model's focus regardless of how well each
            tool is described. Sharper descriptions are a band-aid; fewer, scoped
            tools fix the mechanism.

            *What the code proves vs. what the exam claims:* the replay above shows
            scoping is enforced at dispatch (a wrong pick is refused), which is the part
            you can test without a model. The claim that fewer tools also make the
            *right* pick more likely is the exam's, and it is why the fix is structural.
        """),
    ])


# ---- Notebook 04: Error Handling ----

def gen_04() -> nbformat.NotebookNode:
    return _make_nb([
        _md("""
            # 04 --- Structured Error Handling

            **CCA Pattern**: Subagents return structured error context so the coordinator can
            retry, flag gaps, or adjust confidence.

            **Anti-pattern**: Silent failures return `{"status":"success","data":null}`
            -- the coordinator can't tell if the source was empty or failed.
        """),
        _code(PATH_SHIM),
        _code("""
            import json

            from research_agents.tools.handlers import dispatch
            from research_agents.anti_patterns.silent_failures import handle_fetch_page_silent, silent_dispatch
            from research_agents.agent.coordinator import build_research_report, collect_gaps, run_coordinator
            from research_agents.models.research import SubTask
            from research_agents.services.container import make_default_services
            from research_agents.testing import scripted_client, text_turn, tool_turn

            services = make_default_services()
        """),
        _md("""
            ## The ToolErrorResponse Model

            When a tool handler encounters an error, it returns a `ToolErrorResponse`
            (from `models/errors.py`), serialized through `tools/_errors.error_response()`
            so the JSON on the wire cannot drift from the model:

            ```python
            class ToolErrorResponse(BaseModel):
                status: str = "error"
                error_type: str    # "timeout", "not_found", "rate_limit", etc.
                source: str        # which service/URL failed
                message: str       # human-readable error description
                retry_eligible: bool      # Can the coordinator retry?
                fallback_available: bool   # Is there an alternative source?
                partial_data: dict | None = None  # Any data recovered before failure
            ```

            This gives the coordinator a **decision tree**:
            - `retry_eligible=True` -> retry (timeouts, rate limits)
            - `fallback_available=True` -> try alternative source
            - Both `False` -> flag gap in the final report

            In this package the "flag gap" branch is implemented programmatically
            (`coordinator.collect_gaps()`); retry and fallback are decisions left to the
            caller. The point of the schema is that the coordinator *can* decide.

            ### The Anti-Pattern: SilentFailureResponse

            ```python
            class SilentFailureResponse(BaseModel):
                status: str = "success"  # LIES
                data: None = None         # No data, but claims success
            ```

            The coordinator cannot distinguish between:
            - 'no relevant data exists' (legitimate empty result)
            - 'the subagent failed to retrieve data' (error needing handling)
        """),
        _md("""
            ## Simulated Data: Intentional Failures

            The project's test data (in `data/sources.py`) includes URLs that intentionally fail:

            | URL | Behavior | Purpose |
            |-----|----------|---------|
            | `timeout.example.com/remote-data` | Simulated timeout | Tests retry logic |
            | `healthtech.example.com/ai-revolution` | Simulated 404 | Tests fallback logic |

            Let's see how each handler responds to these failures.
        """),
        _md("## Anti-Pattern: Silent Failure"),
        _code("""
            # Silent failure on timeout -- returns success with null
            silent_result = json.loads(handle_fetch_page_silent(
                {'url': 'https://timeout.example.com/remote-data'}, services
            ))
            print('Silent failure response:')
            print(json.dumps(silent_result, indent=2))
            print(f'\\nCan coordinator tell this was a timeout? {"error_type" in silent_result}')
        """),
        _md("""
            ### Why This Fails: The Silent-Failure Cascade

            The response above is `{"status": "success", "data": null}` -- it looks
            identical to a legitimate empty result, and the coordinator has no way to tell
            them apart. That ambiguity is the whole problem. Now imagine a research
            pipeline where a web fetch silently times out. Downstream steps proceed on the
            empty payload as if it were ground truth. The coordinator synthesizes a
            `ResearchReport` with a plausible confidence score because nothing ever
            reported a failure. The missing source is invisible.

            A single silent failure high in the dependency graph *cascades*: every
            downstream task treats `null` as legitimate, the conflict resolver has no
            contradictions to weigh (because one of the disputing sources never arrived),
            and the final report declares no gaps. The user sees a confident-looking
            answer that is quietly incomplete. This is why the CCA exam's correct
            answer is always "require structured error context" rather than "add retry
            logic" -- retry is one branch of the decision tree, and you cannot build a
            decision tree on a response that refuses to admit failure.

            The cascade is executed, not just described, further down.
        """),
        _md("## Correct Pattern: Structured Error Context"),
        _code("""
            # Structured error on timeout -- coordinator gets full decision tree
            structured_result = json.loads(dispatch(
                'web_researcher', 'fetch_page',
                {'url': 'https://timeout.example.com/remote-data'}, services
            ))
            print('Structured error response:')
            print(json.dumps(structured_result, indent=2))
            print(f'\\nCan coordinator retry? {structured_result.get("retry_eligible")}')
            print(f'Error type: {structured_result.get("error_type")}')
        """),
        _code("""
            # Also show a 404 error (different decision tree)
            not_found_result = json.loads(dispatch(
                'web_researcher', 'fetch_page',
                {'url': 'https://healthtech.example.com/ai-revolution'}, services
            ))
            print('404 error response:')
            print(json.dumps(not_found_result, indent=2))
            print(f'\\nRetry eligible: {not_found_result.get("retry_eligible")}')
            print(f'Fallback available: {not_found_result.get("fallback_available")}')
        """),
        _md("""
            ### The cascade, executed

            One scripted web researcher fetches the timeout URL and then -- as models do
            -- writes a confident summary as if the fetch had worked. The same transcript
            runs through the coordinator twice: once with the silent router injected,
            once with the structured one. `build_research_report()` derives `gaps` from
            the tool results the loop logged, never from the model's prose.
        """),
        _code("""
            TIMEOUT_URL = 'https://timeout.example.com/remote-data'
            tasks = [SubTask(task_id='web', agent_type='web_researcher',
                             instruction='Fetch the remote productivity dataset', context=TIMEOUT_URL)]
            transcript = {'web_researcher': [
                tool_turn('fetch_page', {'url': TIMEOUT_URL}),
                text_turn('Fetched the remote dataset and summarised its productivity figures.'),
            ]}

            def run_pipeline(dispatch_fn):
                results, _ = run_coordinator(scripted_client(transcript), services, tasks,
                                             dispatch_fn=dispatch_fn)
                report = build_research_report('remote work productivity', results, reliability_lookup={})
                return results, report

            silent_results, silent_report = run_pipeline(silent_dispatch)
            structured_results, structured_report = run_pipeline(dispatch)

            print(f'Silent router:     gaps={silent_report.gaps}  confidence={silent_report.confidence_score}')
            print(f'Structured router: gaps={structured_report.gaps}  confidence={structured_report.confidence_score}')
            print()
            print('What the model wrote in both runs:', repr(structured_results['web'].content))
        """),
        _md("""
            The model's summary was identical and equally wrong in both runs. Only the
            structured run produced a report that admits the source was never reached.
            The lower confidence score on the right is the correct outcome: the honest
            report is the one that says less.
        """),
        _code("""
            from helpers import compare_results

            compare_results(
                {'status': silent_result['status'],
                 'has_error_type': 'error_type' in silent_result,
                 'has_retry_eligible': 'retry_eligible' in silent_result,
                 'coordinator_can_retry': silent_result.get('retry_eligible', False),
                 'tool_calls_made': silent_results['web'].tool_calls,
                 'gaps_reported': len(silent_report.gaps),
                 'confidence_score': silent_report.confidence_score},
                {'status': structured_result['status'],
                 'has_error_type': 'error_type' in structured_result,
                 'has_retry_eligible': 'retry_eligible' in structured_result,
                 'coordinator_can_retry': structured_result.get('retry_eligible', False),
                 'tool_calls_made': structured_results['web'].tool_calls,
                 'gaps_reported': len(structured_report.gaps),
                 'confidence_score': structured_report.confidence_score},
            )
        """),
        _md("""
            ## CCA Exam Tip

            > The silent failure question presents a scenario where a report is missing data.
            > - 'increase timeout duration' -- WRONG (addresses symptoms, not root cause)
            > - 'add retry logic' -- WRONG (partially helpful but not the core fix)
            > - **'require structured error context from subagents' -- CORRECT**
            >
            > The key insight: the coordinator needs enough information to make a decision
            (retry, fallback, or flag gap). Silent failures remove that decision-making ability.
        """),
    ])


# ---- Notebook 05: Task Decomposition ----

def gen_05() -> nbformat.NotebookNode:
    return _make_nb([
        _md("""
            # 05 --- Task Decomposition

            **CCA Pattern**: The coordinator decomposes queries into parallel and sequential
            phases based on data dependencies.

            Web search and document analysis can run in parallel. Fact checking depends on their
            results, so it runs after.
        """),
        _code(PATH_SHIM),
        _code("""
            from research_agents.models.research import SubTask
            from research_agents.agent.coordinator import sort_tasks_into_waves
        """),
        _md("""
            ## How `sort_tasks_into_waves()` Works

            The topological sort in `coordinator.py` is straightforward:

            ```python
            def sort_tasks_into_waves(tasks: list[SubTask]) -> list[list[SubTask]]:
                completed: set[str] = set()
                remaining = list(tasks)
                waves: list[list[SubTask]] = []
                while remaining:
                    wave = [t for t in remaining
                            if all(d in completed for d in t.depends_on)]
                    # ... add wave, mark completed, continue
                return waves
            ```

            Each iteration finds all tasks whose dependencies are already completed.
            Those tasks form the next wave and can run in parallel. If no tasks can run
            (circular dependency), all remaining tasks are placed in one wave as a fallback.

            ### The `depends_on` Field

            The `SubTask.depends_on` field is a list of `task_id` strings. This is the
            **only** mechanism that creates sequential ordering. Tasks with empty `depends_on`
            are independent and can run in parallel.
        """),
        _md("""
            ## The Restaurant Kitchen Analogy

            Task decomposition on an exam looks abstract, but the kitchen version makes
            it obvious.

            A brigade kitchen has stations: appetizer, grill, pantry, pastry, and
            expediter. When an order comes in for a steak frites with a caesar salad:

            - The **grill** station cooks the steak and the fries can run in parallel
            at the fry station -- neither needs the other's output.
            - The **pantry** station builds the caesar salad in parallel with both of
            those -- independent inputs, independent tools.
            - The **expediter** plates everything -- and that step must wait for *all*
            stations to finish. The plating `depends_on` every upstream step.

            This is exactly what `sort_tasks_into_waves()` does. Independent stations
            (no `depends_on`) form Wave 0 and work simultaneously. The expediter, who
            needs everything, sits in Wave 1.

            Now picture a kitchen where *nothing* is parallelized -- the same cook has
            to finish the steak before the fries can start, and the fries before the
            salad. Every dish comes out cold. That is the sequential-only anti-pattern.
        """),
        _md("""
            ## Anti-Pattern: Everything Sequential

            Forcing every task to `depends_on` its predecessor -- even when no data
            actually flows between them -- is the most common decomposition mistake
            on the exam. It runs correctly but wastes the coordinator's biggest
            available optimization. The tasks below are identical to the correct
            version further down except for their `depends_on` edges:
        """),
        _code("""
            # ANTI-PATTERN: naive all-sequential decomposition
            # Web search does not need database stats to start.
            # Database stats do not need document analysis to start.
            # But the author chained them anyway.
            naive_tasks = [
                SubTask(task_id='web', agent_type='web_researcher',
                    instruction='Search for remote work studies',
                    context='Focus on 2024'),
                SubTask(task_id='data', agent_type='data_extractor',
                    instruction='Query remote work statistics',
                    context='remote_work_stats table',
                    depends_on=['web']),                  # not actually needed!
                SubTask(task_id='docs', agent_type='document_analyzer',
                    instruction='Parse Stanford study',
                    context='doc-remote-work-stanford',
                    depends_on=['data']),                 # not actually needed!
                SubTask(task_id='facts', agent_type='fact_checker',
                    instruction='Verify claims',
                    context='', depends_on=['web', 'data', 'docs']),  # legitimately dependent
            ]
            naive_waves = sort_tasks_into_waves(naive_tasks)
            print(f'Anti-pattern wave count: {len(naive_waves)} (all single-task waves -- no parallelism)')
            for i, wave in enumerate(naive_waves):
                print(f'  Wave {i}: {[t.task_id for t in wave]}')
        """),
        _md("""
            ### Why This Fails

            Nothing is *wrong* here -- the pipeline still produces the right result.
            It just takes twice as many waves as it needs (4 instead of 2, as the
            comparison below shows). On the exam, any option that chains `depends_on`
            without an actual data dependency is the distractor. The CCA answer always
            asks: *does this task actually need the previous task's output?* If no,
            drop the `depends_on` edge.

            Below is the same research broken into the correct parallel + sequential
            shape. Compare the wave counts.
        """),
        _md("## Correct Pattern: Parallel + Sequential Waves"),
        _code("""
            # Same tasks; only the real data dependency remains
            tasks = [
                SubTask(task_id='web', agent_type='web_researcher',
                    instruction='Search for remote work studies',
                    context='Focus on 2024'),
                SubTask(task_id='data', agent_type='data_extractor',
                    instruction='Query remote work statistics',
                    context='remote_work_stats table'),
                SubTask(task_id='docs', agent_type='document_analyzer',
                    instruction='Parse Stanford study',
                    context='doc-remote-work-stanford'),
                SubTask(task_id='facts', agent_type='fact_checker',
                    instruction='Verify claims',
                    context='', depends_on=['web', 'data', 'docs']),
            ]

            waves = sort_tasks_into_waves(tasks)
            for i, wave in enumerate(waves):
                ids = [t.task_id for t in wave]
                agents = [t.agent_type for t in wave]
                print(f'Wave {i}: {ids}')
                print(f'  Agents: {agents}')
                print(f'  Can run in parallel: {len(wave) > 1}')
                print()
        """),
        _md("""
            ### How the Coordinator Executes Waves

            In `run_coordinator()`, each wave is processed sequentially, but tasks within
            a wave could be parallelized:

            ```python
            for wave in waves:
                for task in wave:  # Could be concurrent
                    context_string = build_subagent_context(task, results)
                    result = run_agent_loop(client, services, context_string, ...)
                    results[task.task_id] = result
            ```

            The current implementation processes tasks within a wave sequentially for
            simplicity, but the wave structure makes it trivial to add concurrency later.
            The key point for the CCA exam is that the **dependency analysis is correct** --
            tasks that can run in parallel are identified.
        """),
        _code("""
            from helpers import compare_results

            compare_results(
                {'tasks': len(naive_tasks),
                 'wave_count': len(naive_waves),
                 'max_parallel_tasks': max(len(w) for w in naive_waves)},
                {'tasks': len(tasks),
                 'wave_count': len(waves),
                 'max_parallel_tasks': max(len(w) for w in waves)},
            )
        """),
        _md("""
            ## CCA Exam Tip

            > Task decomposition questions ask whether two subtasks should run in parallel
            or sequentially.
            > - If Subtask B needs output from Subtask A -> sequential (`depends_on`)
            > - If they work from independent inputs -> parallel (no `depends_on`)
            > - 'Web search' and 'document parsing' are the canonical parallel pair
            > - 'Fact checking' depends on what it checks, so it always runs after
            > - The `SubTask.depends_on` field is the mechanism that creates ordering
        """),
    ])


# ---- Notebook 06: Conflict Resolution ----

def gen_06() -> nbformat.NotebookNode:
    return _make_nb([
        _md("""
            # 06 --- Conflict Resolution

            **CCA Pattern**: The coordinator resolves contradictions using deterministic strategies:
            1. Source reliability ranking
            2. Majority consensus
            3. Flag for human review

            This is programmatic enforcement -- not LLM judgment.
        """),
        _code(PATH_SHIM),
        _code("""
            from research_agents.agent.conflict_resolver import resolve_conflict, RELIABILITY_SCORES
            from research_agents.models.research import SourceReliability
            from research_agents.data.sources import SOURCE_RELIABILITY_RATINGS
        """),
        _md("""
            ## How the Conflict Resolver Works

            The `conflict_resolver.py` module uses **deterministic strategies** -- no LLM
            reasoning at all. This is the CCA principle that programmatic enforcement beats
            prompt-based guidance.

            ### The ConflictRecord Model

            ```python
            class ConflictRecord(BaseModel):
                claim: str                 # The disputed factual claim
                sources_for: list[str]     # URLs supporting the claim
                sources_against: list[str] # URLs contradicting the claim
                resolution: str            # "majority", "highest_reliability", "flagged_for_human"
                confidence: float          # 0.0 to 1.0
                winning_side: str          # "for", "against", or "undecided"
            ```

            `winning_side` matters: a record that only says *how* a conflict was resolved
            is useless to the synthesis step, which needs to know *which way*.

            ### Reliability Scoring

            Sources are scored by reliability tier:

            | Tier | Score | Examples |
            |------|-------|---------|
            | HIGH | 3 | `.gov`, peer-reviewed journals, official statistics |
            | MEDIUM | 2 | Established news outlets, `.edu`, consultancies |
            | LOW | 1 | Blogs, unverified sources |
            | UNKNOWN | 0 | Not yet assessed |

            Ratings are keyed by domain (`"energy.gov"`) and sources arrive as full URLs;
            the resolver matches them the same way the knowledge base does, so
            `SOURCE_RELIABILITY_RATINGS` can be passed straight in.

            ### Three-Tier Resolution Strategy

            1. **Reliability ranking**: Compare the *best* tier on each side. The side
            with the more reliable source wins; three blogs never outrank one `.gov`.
            Confidence scales with the tier gap: `0.5 + gap * 0.15`, capped at 0.95.
            2. **Majority consensus**: If the best tiers are equal, the side with more
            sources wins. Confidence = majority_size / total, capped at 0.85.
            3. **Human review**: If both tier and count tie, flag for human review
            with low confidence (0.3).
        """),
        _md("""
            ## Anti-Pattern: First Result Wins

            The distractor on the exam is "take whichever source came back first". It
            is simple and it *feels* decisive. It is also a function of arrival order,
            which is a function of network latency, which has nothing to do with truth.
            The cell below shows the verdict flipping when the same three reports arrive
            in a different order.
        """),
        _code("""
            GOV = 'https://bls.gov/remote-work-stats'
            MCKINSEY = 'https://mckinsey.com/future-of-work'
            BLOG = 'https://workfromhome-blog.example.com/productivity'
            CLAIM = 'Remote workers are more productive'

            def domain(url: str) -> str:
                return url.split('/')[2]

            def first_result_wins(reports: list[tuple[str, str]]) -> str:
                \"\"\"ANTI-PATTERN: whichever source reported first decides the claim.\"\"\"
                source, stance = reports[0]
                print(f'  (decided by {domain(source)})')
                return stance

            blog_first = [(BLOG, 'against'), (MCKINSEY, 'for'), (GOV, 'for')]
            gov_first = list(reversed(blog_first))

            anti_a = first_result_wins(blog_first)
            print(f'Blog reports first -> verdict: {anti_a}')
            anti_b = first_result_wins(gov_first)
            print(f'.gov reports first -> verdict: {anti_b}')
            print(f'Same evidence, same verdict? {anti_a == anti_b}')
        """),
        _md("""
            ## Correct Pattern: Deterministic Resolution

            `resolve_conflict()` takes the evidence sorted by stance, not by arrival, and
            scores it by reliability. The same three reports give the same verdict in
            either order.
        """),
        _code("""
            def deterministic_verdict(reports: list[tuple[str, str]]) -> tuple[str, object]:
                sources_for = [s for s, stance in reports if stance == 'for']
                sources_against = [s for s, stance in reports if stance == 'against']
                record = resolve_conflict(CLAIM, sources_for, sources_against, SOURCE_RELIABILITY_RATINGS)
                return record.winning_side, record

            correct_a, record_a = deterministic_verdict(blog_first)
            correct_b, record_b = deterministic_verdict(gov_first)
            print(f'Blog reports first -> verdict: {correct_a}  ({record_a.resolution}, {record_a.confidence:.2f})')
            print(f'.gov reports first -> verdict: {correct_b}  ({record_b.resolution}, {record_b.confidence:.2f})')
            print(f'Same evidence, same verdict? {correct_a == correct_b}')
        """),
        _md("## Strategy 1: Source Reliability Ranking"),
        _code("""
            # Show the scoring constants
            print('Reliability scores:')
            for tier, score in RELIABILITY_SCORES.items():
                print(f'  {tier.value:<10s} = {score}')
            print()

            # High-reliability source beats low-reliability (ratings keyed by domain)
            record = resolve_conflict(
                claim='Renewable energy accounts for 30% of global electricity',
                sources_for=['https://energy.gov/renewable-2024'],
                sources_against=['https://energyblog.example.com/renewables'],
                reliability_lookup=SOURCE_RELIABILITY_RATINGS,
            )
            print(f'Claim: {record.claim}')
            print(f'Resolution: {record.resolution}')
            print(f'Winning side: {record.winning_side}')
            print(f'Confidence: {record.confidence:.2f}  # HIGH(3) vs LOW(1): gap 2 -> 0.5 + 2 * 0.15')
        """),
        _md("""
            ## Strategy 2: Majority Vote (when reliabilities tie)

            If the best tier is the same on both sides, the resolver falls through to a
            majority vote. This matters in the most common real-world case: several
            moderately-reliable news outlets disagreeing with each other. No one side has
            a reliability edge, but three sources saying the same thing is stronger
            evidence than one source saying the opposite.

            The confidence on a majority resolution is `majority_count / total_count`.
            So 3 of 4 sources agreeing yields `0.75`. This is deliberately lower than
            the confidence ceiling on reliability wins (`0.95`) -- a reliability-based
            answer is treated as stronger evidence than a count-based answer, which
            is what you'd want on the exam.
        """),
        _code("""
            # Three medium-reliability sources for the claim, one against
            reliability_majority = {
                'https://reuters.com/article-a': SourceReliability.MEDIUM,
                'https://bbc.com/article-b': SourceReliability.MEDIUM,
                'https://apnews.com/article-c': SourceReliability.MEDIUM,
                'https://nytimes.com/article-d': SourceReliability.MEDIUM,
            }
            majority_record = resolve_conflict(
                claim='Hybrid work arrangements increase employee retention',
                sources_for=[
                    'https://reuters.com/article-a',
                    'https://bbc.com/article-b',
                    'https://apnews.com/article-c',
                ],
                sources_against=['https://nytimes.com/article-d'],
                reliability_lookup=reliability_majority,
            )
            print(f'Resolution: {majority_record.resolution}')
            print(f'Winning side: {majority_record.winning_side}')
            print(f'Confidence: {majority_record.confidence:.2f}  # 3 of 4 sources agree -> 0.75')
            print(f'Sources for: {len(majority_record.sources_for)}, against: {len(majority_record.sources_against)}')
        """),
        _md("## Strategy 3: Equal Reliability + Equal Count -> Human Review"),
        _code("""
            # Equal reliability + equal count -> human review
            reliability_equal = {
                'https://reuters.com': SourceReliability.MEDIUM,
                'https://bbc.com': SourceReliability.MEDIUM,
            }
            record2 = resolve_conflict(
                claim='Remote work productivity',
                sources_for=['https://reuters.com'],
                sources_against=['https://bbc.com'],
                reliability_lookup=reliability_equal,
            )
            print(f'Resolution: {record2.resolution}')
            print(f'Winning side: {record2.winning_side}')
            print(f'Confidence: {record2.confidence:.2f}')
        """),
        _code("""
            from helpers import compare_results

            compare_results(
                {'verdict_when_blog_reports_first': anti_a,
                 'verdict_when_gov_reports_first': anti_b,
                 'order_independent': anti_a == anti_b},
                {'verdict_when_blog_reports_first': correct_a,
                 'verdict_when_gov_reports_first': correct_b,
                 'order_independent': correct_a == correct_b},
            )
        """),
        _md("""
            ### How This Connects to the ResearchReport

            The `build_research_report()` function in `coordinator.py` uses conflict records
            to adjust the report's overall confidence score:

            ```python
            base_confidence = 0.8
            if gaps:
                base_confidence -= 0.1 * len(gaps)     # Each gap reduces confidence
            if conflict_records:
                flagged = [c for c in conflict_records
                           if c.resolution == "flagged_for_human"]
                base_confidence -= 0.05 * len(flagged)  # Unresolved conflicts reduce confidence
            ```

            Reports that say 'we could not reach Source X' or 'these sources disagree and we
            flagged it for human review' are **more trustworthy** than reports that silently
            omit unavailable sources or pick the first result.
        """),
        _md("""
            ## CCA Exam Tip

            > The conflict resolution question tests whether you understand that:
            > - Source reliability ranking is the first strategy
            > - Majority consensus applies when reliability is tied
            > - Human review is the fallback, not auto-resolution
            > - 'First result wins' is always the wrong answer
            > - The resolution is **deterministic** -- same inputs always produce same output

            *Why deterministic?* Enterprise systems need **predictable, auditable,
            repeatable** outcomes -- a resolution must be reviewable after the fact
            and reproducible for compliance. LLM judgment cannot meet those three
            requirements; programmatic rules can.
        """),
    ])


# ---- Notebook 07: MCP Primitives ----

def gen_07() -> nbformat.NotebookNode:
    return _make_nb([
        _md("""
            # 07 --- MCP Primitives

            **CCA Pattern**: MCP (Model Context Protocol) servers expose three primitives:
            - **Tools** -- executable functions an agent can invoke (verbs)
            - **Resources** -- data the application can read and hand to the model (nouns)
            - **Prompts** -- reusable, parameterized message templates (patterns)

            The exam tests whether you know the difference.
        """),
        _code(PATH_SHIM),
        _code("""
            import json

            from research_agents.tools.definitions import ALL_TOOL_SETS
            from research_agents.tools.handlers import dispatch
            from research_agents.agent.subagents import WEB_RESEARCHER_PROMPT
            from research_agents.services.container import make_default_services

            services = make_default_services()
        """),
        _md("""
            ## Understanding the Three MCP Primitives

            MCP is a protocol that standardizes how AI agents interact with external systems.
            The CCA exam tests your ability to classify capabilities into the correct primitive.

            ### The Key Distinction

            | Primitive | Nature | Analogy | Example |
            |-----------|--------|---------|--------|
            | **Tool** | Action (verb) | Function call | `verify_claim(claim)` |
            | **Resource** | Data (noun) | Database query | Source reliability ratings |
            | **Prompt** | Template (pattern) | Reusable format | Research query decomposition |

            ### Who is in control

            The MCP specification's strongest classification tell is *who decides to use
            the primitive* (Server features, "Control hierarchy"):

            | Primitive | Controlled by | Meaning |
            |-----------|---------------|---------|
            | **Prompts** | User | Exposed for the user to pick explicitly (slash commands, menus) |
            | **Resources** | Application | The host app decides what context to attach for the model |
            | **Tools** | Model | The model decides to call them, subject to human approval |

            The most common exam mistake is classifying a **Resource** as a **Tool**.
            A source reliability database is *data the application can read* (Resource),
            not *an action the model chooses to perform* (Tool).

            ### How Our System Maps to MCP

            Our project uses the `anthropic` SDK directly (not the Agent SDK), so MCP primitives
            are represented as plain Python constructs. Here's how each maps:
        """),
        _md("## Tools (Verbs) -- Things the Agent Does"),
        _code("""
            # Our tool definitions are MCP Tools -- executable functions
            for agent_type, tools in ALL_TOOL_SETS.items():
                print(f'{agent_type}:')
                for tool in tools:
                    print(f'  Tool: {tool["name"]:<25s} (action/verb)')
        """),
        _md("""
            Each tool above is an **action** the agent can invoke. `search_web` performs a search.
            `verify_claim` checks a claim. `delegate_task` triggers delegation. These are verbs.

            In MCP terms, each tool definition has:
            - A `name` (the function to call)
            - A `description` (what it does and does NOT do)
            - An `input_schema` (the parameters it accepts)

            Calling one performs computation and returns a result:
        """),
        _code("""
            verdict = json.loads(dispatch('fact_checker', 'verify_claim',
                                          {'claim': 'Remote workers are 13% more productive'}, services))
            print(json.dumps(verdict['data'], indent=2))
        """),
        _md("""
            ## Resources (Nouns) -- Things the Agent Reads

            In our system these are read-only service methods. In an MCP server each would
            be exposed as a resource identified by a URI. The scheme is the server's
            choice -- `file://`, `https://`, or something custom like `kb://` -- and the
            client reads it with `resources/read`. Reading a resource has no side effects.
        """),
        _code("""
            kb = services.knowledge_base
            docs = services.document_store
            db = services.database

            resources = {
                'kb://sources/reliability': kb.get_source_reliability('https://energy.gov/renewable-2024').value,
                'docs://catalog': [d.doc_id for d in docs.list_documents()],
                'db://schemas/remote_work_stats': [c['name'] for c in db.get_schema('remote_work_stats')['columns']],
            }
            for uri, value in resources.items():
                print(f'  Resource {uri:<32s} -> {value}')
        """),
        _md("""
            These are **data** the application queries, not actions the model performs.
            In our codebase:

            - `kb://sources/reliability` -> `KnowledgeBase.get_source_reliability()`
            returns a `SourceReliability` enum
            - `docs://catalog` -> `DocumentStore.list_documents()` returns document metadata
            - `db://schemas/...` -> `DatabaseService.get_schema()` returns column definitions
        """),
        _md("## Prompts (Patterns) -- Templates the Agent Uses"),
        _code("""
            # Prompts in our system (conceptual mapping)
            prompts = {
                'research_query_template': 'Template for decomposing a query into subtasks',
                'citation_format_template': 'Template for formatting citations (APA)',
                'error_report_template': 'Template for reporting structured errors',
            }
            for name, desc in prompts.items():
                print(f'  Prompt: {name:<30s} -- {desc}')
            print()
            print('Closest thing in this codebase (a system prompt, not an MCP Prompt):')
            print(WEB_RESEARCHER_PROMPT[:160].strip() + '...')
        """),
        _md("""
            In our codebase, these map to:

            - `research_query_template` -> The system prompts in `subagents.py`
            (e.g., `WEB_RESEARCHER_PROMPT`)
            - `citation_format_template` -> Would be an MCP Prompt if we needed
            configurable citation styles
            - `error_report_template` -> The `ToolErrorResponse` model structure

            In MCP, Prompts are reusable templates that can be invoked with parameters.
            They're not system prompts -- they're parameterized message templates
            that standardize common operations, and the *user* chooses when to apply one.
        """),
        _md("""
            ## Classification Exercise

            Five items below. For each, decide whether it is a **Tool**, a **Resource**,
            or a **Prompt** *before* reading the worked answer in the cell that follows.
            The CCA exam rewards snap classification, so practice making the call first.
        """),
        _md("""
            ### Item 1 -- `verify_claim(claim: str)` returning `{verified, confidence, source}`

            Your classification?

            <details>
            <summary>Reveal the answer</summary>

            **Tool.** It performs an action: looking the claim up in the knowledge base,
            ranking the matches, and scoring the result. The model decides when to call
            it. Anything shaped like a function call with an imperative verb in the name
            is almost always a Tool.

            Trap to avoid: candidates sometimes classify it as a Resource because it
            "returns information." Tools also return information -- the distinguishing
            feature is *computation the model triggers*, not read-only access.

            </details>
        """),
        _md("""
            ### Item 2 -- A database of source URLs with reliability ratings

            Your classification?

            <details>
            <summary>Reveal the answer</summary>

            **Resource.** It is read-only data. In MCP, the server would expose it under a
            URI of its choosing (say `kb://sources/reliability`) and the application would
            *read* it with `resources/read` rather than have the model *call* it.

            This is **the** canonical exam trap. Options include
            `get_source_reliability(url)` (a Tool-like wrapper) as a distractor. The
            underlying capability is a Resource even if the access pattern looks
            Tool-shaped. The exam question is usually worded in terms of the data
            itself ("a database of ratings"), which is the tell.

            </details>
        """),
        _md("""
            ### Item 3 -- A template for decomposing a research query into SubTasks

            Your classification?

            <details>
            <summary>Reveal the answer</summary>

            **Prompt.** It is a reusable pattern, parameterized by the incoming query,
            that produces a structured decomposition. Prompts in MCP are not system
            prompts -- they are *parameterized message templates* a user can invoke to
            standardize common operations.

            If you said "Tool" because it produces an output: Prompts also produce
            outputs. The distinguishing feature of a Prompt is that it is a
            *template* with named parameters, not a function with computation.

            </details>
        """),
        _md("""
            ### Item 4 -- `fetch_page(url: str) -> PageContent`

            Your classification?

            <details>
            <summary>Reveal the answer</summary>

            **Tool.** It performs the action of fetching a page and has observable side
            effects (network call, possible failure modes). This is the easiest kind of
            item on the exam -- clear verb, clear parameter, clear return type. If it
            can time out or fail, it is almost certainly a Tool (Resources are usually
            read-only and cacheable in a way that fetch calls are not).

            </details>
        """),
        _md("""
            ### Item 5 -- A catalog listing available research documents with metadata

            Your classification?

            <details>
            <summary>Reveal the answer</summary>

            **Resource.** A catalog is data the agent browses. The items in it may be
            things the agent can act on, but the catalog *itself* is a Resource.

            Watch this distinction on the exam: `list_documents()` is often listed as a
            Tool, but the underlying "available documents" is the Resource. If the
            question asks about the *capability*, go Resource. If it asks about the
            *function exposed to the agent*, the answer might be Tool. Read carefully.

            </details>
        """),
        _md("""
            ## CCA Exam Tip

            > The MCP primitives question is a vocabulary test:
            > - **Tools** are things the agent *does* (verbs) -- model-controlled
            > - **Resources** are things the application *reads* for the model (nouns) -- application-controlled
            > - **Prompts** are templates the *user* invokes (patterns) -- user-controlled
            >
            > If a question describes a source reliability database -> **Resource**, not a Tool.
            > If it describes a function that verifies a claim -> **Tool**.
            > If it describes a reusable template for formatting citations -> **Prompt**.
            >
            > The most common distractor makes a Resource look like a Tool because
            both involve 'getting information.' The difference: Tools have **side effects**
            or perform **computation**; Resources are **read-only data**.

            *Foolproof test:* **if you cannot *run* it, it is probably a Resource.**
            A Tool *performs an action* (e.g., `fetch_page(url)`, `verify_claim(claim)`)
            -- often *using* a Resource. A Resource is the *data or infrastructure the
            Tool acts upon* (e.g., a database of sources, a schema catalog, a file
            system). Same information can appear behind either primitive -- ask which
            side of the verb it sits on, and who decides to use it.
        """),
    ])


# ---- Notebook 08: Integration ----

def gen_08() -> nbformat.NotebookNode:
    return _make_nb([
        _md("""
            # 08 --- Integration: Full End-to-End Research Query

            This notebook brings together all CCA patterns:
            - Hub-and-spoke coordinator
            - Context isolation via explicit passing
            - 4-5 scoped tools per agent
            - Structured error handling
            - Parallel + sequential task waves
            - Deterministic conflict resolution

            We'll walk through a complete research query using the `economic_impact` scenario.
            Four scripted subagents each call real tools through the real loop; one fetch
            times out and the fact checker flags a contradiction, so every step of the
            6-step flow has something to do.
        """),
        _code(PATH_SHIM),
        _code("""
            import json

            from research_agents.models.research import SubTask
            from research_agents.agent.coordinator import (
                build_research_report, collect_gaps, collect_tool_errors, run_coordinator, sort_tasks_into_waves,
            )
            from research_agents.agent.context_builder import build_subagent_context
            from research_agents.anti_patterns.silent_failures import silent_dispatch
            from research_agents.data.scenarios import SCENARIOS
            from research_agents.data.sources import SOURCE_RELIABILITY_RATINGS
            from research_agents.services.container import make_default_services
            from research_agents.testing import scripted_client, text_turn, tool_turn
            from research_agents.tools.handlers import dispatch
        """),
        _md("""
            ## The ResearchScenario Model

            The project defines pre-built scenarios (in `data/scenarios.py`) that combine
            all the patterns we've studied:

            ```python
            @dataclass(frozen=True)
            class ResearchScenario:
                name: str
                query: str
                expected_agents: list[str]  # Which agent types should be involved
                expected_conflicts: int     # How many source contradictions
                expected_gaps: int          # How many sources will fail
                description: str
            ```

            Three scenarios, each targeting different patterns:

            | Scenario | Tests | Conflicts | Gaps |
            |----------|-------|-----------|------|
            | `climate_renewable` | Conflict resolution | 1 (blog vs .gov) | 0 |
            | `ai_healthcare` | Error handling | 0 | 1 (404) |
            | `economic_impact` | Both | 1 (+13% vs -20%) | 1 (timeout) |
        """),
        _md("## Scenario: Remote Work Economic Impact\n\nThis scenario tests both conflict resolution AND error handling."),
        _code("""
            scenario = SCENARIOS['economic_impact']
            print(f'Query: {scenario.query}')
            print(f'Expected agents: {scenario.expected_agents}')
            print(f'Expected conflicts: {scenario.expected_conflicts}')
            print(f'Expected gaps: {scenario.expected_gaps}')
            print(f'Description: {scenario.description}')
        """),
        _md("""
            ## Step 1: Task Decomposition (PLAN + SORT)

            The coordinator decomposes the query into SubTasks. In production the LLM does
            this; the package leaves it to the caller. Here we define them explicitly to
            show the structure:
        """),
        _code("""
            # Decompose into subtasks (normally the LLM does this)
            tasks = [
                SubTask(task_id='web', agent_type='web_researcher',
                    instruction='Search for studies on remote work and productivity',
                    context='Focus on 2024 data. Look for both pro and con evidence.'),
                SubTask(task_id='data', agent_type='data_extractor',
                    instruction='Query remote work statistics from the database',
                    context='Use the remote_work_stats table'),
                SubTask(task_id='docs', agent_type='document_analyzer',
                    instruction='Analyze the Stanford remote work study',
                    context='Document ID: doc-remote-work-stanford'),
                SubTask(task_id='facts', agent_type='fact_checker',
                    instruction='Verify productivity claims and flag contradictions',
                    context='Check claims about remote work productivity impact',
                    depends_on=['web', 'data', 'docs']),
            ]

            waves = sort_tasks_into_waves(tasks)
            for i, wave in enumerate(waves):
                print(f'Wave {i}: {[t.task_id for t in wave]} ({"parallel" if len(wave) > 1 else "sequential"})')
        """),
        _md("""
            ## Step 2: Context Isolation Check (DELEGATE)

            Each subagent gets ONLY its explicit context. Wave-0 tasks have no
            predecessors, so their context is just instruction + context. (The `facts`
            task will also receive its three predecessors' results at run time; the
            coordinator adds those, filtered by `depends_on`.)
        """),
        _code("""
            for task in tasks:
                ctx = build_subagent_context(task)
                print(f'{task.task_id} ({task.agent_type}):')
                print(f'  Context length: {len(ctx)} chars')
                print(f'  First 100 chars: {ctx[:100]}...')
                print()
        """),
        _md("""
            ## Step 3: Run Coordinator (scripted transcripts)

            No API call is made. Each agent type gets a scripted transcript -- the tool
            calls a model would make, then its summary -- and `run_coordinator()` does
            everything else for real: context building, scoped tools, dispatch, tool
            results, message history. The transcript is chosen per call from the *tools*
            the coordinator passed, which is itself a check that each agent received its
            own scoped set.

            ```python
            def run_coordinator(client, services, tasks, model, max_iterations, dispatch_fn):
                waves = sort_tasks_into_waves(tasks)
                for wave in waves:
                    for task in wave:
                        config = SUBAGENT_CONFIGS[task.agent_type]
                        context = build_subagent_context(task, results)
                        result = run_agent_loop(client, services, context, ..., dispatch_fn=dispatch_fn)
                        results[task.task_id] = result
                return results, waves
            ```

            Note the web researcher's script: it fetches the timeout URL and then writes a
            summary that mentions nothing about a failure. The report must not trust that.
        """),
        _code("""
            TIMEOUT_URL = 'https://timeout.example.com/remote-data'
            MCKINSEY = 'https://mckinsey.com/future-of-work'
            BLS = 'https://bls.gov/remote-work-stats'
            BLOG = 'https://workfromhome-blog.example.com/productivity'

            transcripts = {
                'web_researcher': [
                    tool_turn('search_web', {'query': 'remote work economic impact on productivity'}),
                    tool_turn('fetch_page', {'url': TIMEOUT_URL}),
                    text_turn('Found 4 sources. McKinsey reports +13% productivity; a blog claims -20%.'),
                ],
                'data_extractor': [
                    tool_turn('query_database', {'table': 'remote_work_stats'}),
                    text_turn('Remote work stats: 9.4% fully remote, 18.2% hybrid in 2024.'),
                ],
                'document_analyzer': [
                    tool_turn('parse_document', {'doc_id': 'doc-remote-work-stanford'}),
                    text_turn('Stanford study: hybrid workers 13% more productive, 24% higher satisfaction.'),
                ],
                'fact_checker': [
                    tool_turn('verify_claim', {'claim': 'Remote workers are 20% less productive'}),
                    tool_turn('flag_conflict', {'claim': 'Remote workers are more productive',
                                                'sources_for': [MCKINSEY, BLS],
                                                'sources_against': [BLOG]}),
                    text_turn('Verified: +13% claim supported. -20% claim contradicted by the knowledge base.'),
                ],
            }

            services = make_default_services()
            client = scripted_client(transcripts)
            results, waves = run_coordinator(client, services, tasks)

            for task_id, result in results.items():
                print(f'{task_id}: {result.tool_calls} tool call(s), stop_reason={result.stop_reason}')
                print(f'   {result.content}')
            print()
            print(f'Tools per API call: {sorted({len(c["tools"]) for c in client.calls})}')
        """),
        _md("""
            ## Step 4: EVALUATE -- what the fact checker's tools returned

            The fact checker is the EVALUATE step: it runs in wave 1 with the others'
            results in its context, verifies a claim against the knowledge base, and flags
            the contradiction. Its tool results are the coordinator's input for RESOLVE.
            Note the `verify_claim` verdict: the blog's -20% claim comes back
            `verified: false` because the knowledge base ranks the closest matching
            record, not the most confident one.
        """),
        _code("""
            for entry in results['facts'].tool_results:
                data = json.loads(entry['result'])['data']
                print(f"{entry['tool_name']}: {json.dumps(data)[:150]}...")

            def conflicts_from(results) -> list[dict]:
                \"\"\"Conflicts the fact checker flagged, read from its tool results.\"\"\"
                return [
                    {k: json.loads(e['result'])['data'][k] for k in ('claim', 'sources_for', 'sources_against')}
                    for e in results['facts'].tool_results
                    if e['tool_name'] == 'flag_conflict'
                ]

            conflicts = conflicts_from(results)
            print()
            print(f'Conflicts flagged: {len(conflicts)}')
            print(f'Tool errors seen by the coordinator: {collect_tool_errors(results)}')
            print(f'Gaps derived from them: {collect_gaps(results)}')
        """),
        _md("""
            ## Steps 5-6: Conflict Resolution + Report (RESOLVE + SYNTHESIZE)

            The `build_research_report()` function compiles findings, resolves conflicts,
            and produces a `ResearchReport`:

            ```python
            class ResearchReport(BaseModel):
                query: str
                findings: list[SourceResult]       # One per subagent transcript
                conflicts: list[ConflictRecord]     # What contradicted, and which side won
                synthesis: str                      # Combined narrative
                confidence_score: float             # 0.0-1.0, adjusted by gaps/conflicts
                gaps: list[str]                     # What we couldn't reach (from tool errors)
            ```

            `gaps` is not passed in below: the report derives it from the structured tool
            errors. `SOURCE_RELIABILITY_RATINGS` is keyed by domain and the conflict's
            sources are full URLs; the resolver matches them.
        """),
        _code("""
            report = build_research_report(
                query=scenario.query,
                results=results,
                reliability_lookup=SOURCE_RELIABILITY_RATINGS,
                conflicts=conflicts,
            )

            print(f'Query: {report.query}')
            print(f'Findings: {len(report.findings)}')
            print(f'Conflicts resolved: {len(report.conflicts)}')
            for c in report.conflicts:
                print(f'  - {c.claim}: {c.resolution}, winning side = {c.winning_side} (confidence: {c.confidence:.2f})')
            print(f'Gaps: {report.gaps}')
            print(f'Confidence score: {report.confidence_score:.2f}')
        """),
        _md("""
            ## Comparison: the same run through the silent-failure router

            Every transcript is replayed unchanged; only the router the coordinator
            injects into the loop differs. The tool call counts and the conflict
            resolution come out identical (the silent router only hides web fetch
            failures), so the one variable is whether the timeout is *visible*.
        """),
        _code("""
            from helpers import compare_results

            silent_results, _ = run_coordinator(scripted_client(transcripts), make_default_services(), tasks,
                                                dispatch_fn=silent_dispatch)
            silent_report = build_research_report(scenario.query, silent_results, SOURCE_RELIABILITY_RATINGS,
                                                  conflicts=conflicts_from(silent_results))

            compare_results(
                {'tool_calls': sum(r.tool_calls for r in silent_results.values()),
                 'timeout_visible_to_coordinator': len(collect_tool_errors(silent_results)) > 0,
                 'gaps_reported': len(silent_report.gaps),
                 'conflict_resolution': silent_report.conflicts[0].resolution,
                 'confidence_score': silent_report.confidence_score},
                {'tool_calls': sum(r.tool_calls for r in results.values()),
                 'timeout_visible_to_coordinator': len(collect_tool_errors(results)) > 0,
                 'gaps_reported': len(report.gaps),
                 'conflict_resolution': report.conflicts[0].resolution,
                 'confidence_score': report.confidence_score},
            )
        """),
        _md("""
            ## How the Pieces Connect

            Here's the complete data flow we just executed:

            ```
            ResearchQuery("remote work productivity")
              |                                              CCA Domain
              v                                              ---------
              1. PLAN: Decompose into 4 SubTasks             Agentic Architecture
              |    (web, data, docs, facts) -- by the caller
              v
              2. SORT: Topological sort into 2 waves          Agentic Architecture
              |    Wave 0: [web, data, docs] (parallel)
              |    Wave 1: [facts] (depends on web, data, docs)
              v
              3. DELEGATE: For each task:                     Context Management
              |    build_subagent_context() -> explicit string
              |    run_agent_loop() with scoped tools          Tool Design
              |    tool errors logged in AgentResult.tool_results
              v
              4. EVALUATE: fact_checker verifies + flags       Reliability
              |    flag_conflict results -> conflicts
              v
              5. RESOLVE: conflict_resolver.py                 Reliability
              |    reliability ranking -> majority -> human, with winning_side
              v
              6. SYNTHESIZE: ResearchReport                    All domains
                   findings + conflicts + gaps (from tool errors) + confidence
            ```
        """),
        _md("""
            ## The Three Exam Walkthrough Questions

            The published article walks through three representative CCA exam questions
            drawn from the multi-agent research scenario. You have now seen every pattern
            they test. Use these as cold-read self-checks.

            Each question below lists the scenario, the correct answer (with a pointer to
            the notebook that demonstrates it), and the distractors you'll see on the
            actual exam along with *why* each distractor is wrong.
        """),
        _md("""
            ### Question 1 -- Context Isolation

            **Scenario.** A user instructs the coordinator to "use APA citation format."
            The web-research subagent returns sources formatted in MLA. Why?

            **Correct answer.** The APA instruction lived in the coordinator's message
            history but was never placed into the subagent's `task.context`. The
            subagent structurally never saw it. The fix is to include formatting
            requirements in every `SubTask.context` where they apply.

            **Where to see it.** Notebook 02 (`02_context_isolation.ipynb`) -- three
            subagents run through the real loop with a recording client: the leaky
            `run_leaky_subagent`, the "forgot to forward" case, and the explicit
            `build_subagent_context(task)` fix. The comparison table reads what each was
            actually sent.

            **Distractors and why they fail:**

            - *"The subagent needs a better system prompt."* The system prompt is a
            general persona, not a place for query-specific requirements. Putting APA in
            every system prompt ever written is not context engineering.
            - *"Use a larger model for the subagent."* A larger model that still never
            sees the instruction will make the same error more fluently.
            - *"Let subagents inherit coordinator context automatically."* This is the
            `shared_context.py` anti-pattern -- it creates token waste, attention
            dilution, and privacy-style leakage of other agents' results.
        """),
        _md("""
            ### Question 2 -- Tool Overload

            **Scenario.** An agent configured with 18 tools repeatedly selects the wrong
            tool for the task. What do you change?

            **Correct answer.** Decompose the single agent into specialized subagents
            with 4-5 focused tools each. This is an **architectural** fix -- it is not
            a better-descriptions problem.

            **Where to see it.** Notebook 03 (`03_tool_scoping.ipynb`) -- lists
            `SUPER_AGENT_TOOLS` (20 on one agent) against the four subagents' sets (4
            each), then replays one out-of-scope tool call through both routers: the
            super agent executes it, scoped `dispatch` refuses it.
            `tests/test_anti_patterns.py` asserts the super-agent count is 20;
            `tests/test_tools.py` asserts the focused sets are exactly 4.

            **Distractors and why they fail:**

            - *"Improve the tool descriptions."* Canonical trap. Better descriptions on
            18 overlapping tools still cause attention fragmentation; the agent spends
            context budget evaluating descriptions rather than executing.
            - *"Add a tool-selection preprocessing step."* You have added a second
            agent to hide the first agent's problem. Now you have two agents to debug
            and the underlying attention-fragmentation still exists during selection.
            - *"Raise the temperature so the agent is less deterministic."* Actively
            harmful -- tool selection should be *more* deterministic, not less.
        """),
        _md("""
            ### Question 3 -- Silent Failure

            **Scenario.** A research report is missing a critical source after an
            upstream API timeout. No error was flagged in the pipeline. What do you
            change?

            **Correct answer.** Require **structured error context** from subagents.
            Every tool handler returns a `ToolErrorResponse` with `error_type`,
            `retry_eligible`, `fallback_available`, and `source`. This gives the
            coordinator a decision tree: retry transient failures, fallback for
            permanent errors, flag gaps in the final report otherwise.

            **Where to see it.** Notebook 04 (`04_error_handling.ipynb`) --
            `handle_fetch_page_silent` vs the structured `dispatch` on the same timeout
            URL, the 404 URL which produces a *different* decision tree, and the cascade
            cell where the same transcript yields `gaps=[]` through the silent router and a
            named gap through the structured one. The comparison at the end of this
            notebook is the same experiment on the full four-agent run. Verified in
            `tests/test_error_handling.py` and `tests/test_coordinator.py`.

            **Distractors and why they fail:**

            - *"Increase timeout duration."* Symptom fix. The next slow service still
            fails silently; you have just moved the threshold.
            - *"Add retry logic."* Partially correct -- retry is *one branch* of the
            decision tree. It does not help when the failure is a 404 or a permanent
            auth error. You cannot build the full decision tree on a response that
            refuses to admit failure.
            - *"Let the coordinator infer failures from response shape."* Requires the
            coordinator to know every subagent's internal contract. Brittle. The
            `ToolErrorResponse` schema makes the contract explicit and uniform.
        """),
        _md("""
            ## CCA Exam Tip

            > The Multi-Agent Research System scenario draws from the three heaviest domains:
            > - Agentic Architecture (27%)
            > - Tool Design & MCP (18%)
            > - Context Management & Reliability (15%)
            >
            > Together: **60% of the exam weight**. Master these patterns and you have a
            framework for every scenario.
            >
            > Key models to know:
            > - `SubTask` -- the unit of delegation with explicit context
            > - `ToolErrorResponse` -- structured errors for informed decision-making
            > - `ConflictRecord` -- deterministic resolution metadata, including which side won
            > - `ResearchReport` -- transparent output with gaps and confidence
        """),
    ])


def main() -> None:
    NOTEBOOKS_DIR.mkdir(exist_ok=True)
    print("Generating notebooks...")
    notebooks = build_all()
    for name, nb in notebooks.items():
        path = NOTEBOOKS_DIR / name
        with open(path, "w") as f:
            nbformat.write(nb, f)
        print(f"  Generated {path}")
    print(f"\nDone! {len(notebooks)} notebooks generated in {NOTEBOOKS_DIR}")


if __name__ == "__main__":
    main()
