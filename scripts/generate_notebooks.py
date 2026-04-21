"""Generate all teaching notebooks programmatically via nbformat.

This ensures notebooks have consistent structure and are always in sync
with the codebase. Re-run this script to regenerate after code changes.
"""

from __future__ import annotations

import nbformat
from pathlib import Path

NOTEBOOKS_DIR = Path(__file__).parent.parent / "notebooks"


def _md(text: str) -> nbformat.NotebookNode:
    return nbformat.v4.new_markdown_cell(text)


def _code(source: str, skip: bool = False) -> nbformat.NotebookNode:
    cell = nbformat.v4.new_code_cell(source)
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


def _save(nb, name: str) -> None:
    path = NOTEBOOKS_DIR / name
    with open(path, "w") as f:
        nbformat.write(nb, f)
    print(f"  Generated {path}")


# ---- Notebook 00: Setup ----

def gen_00():
    nb = _make_nb([
        _md(
            "# 00 --- Setup\n\n"
            "Verify your environment is ready for the CCA Multi-Agent Research System notebooks.\n\n"
            "## Why This Scenario Is 60% of Exam Weight\n\n"
            "> Before you run the imports: understand why this particular scenario matters "
            "disproportionately. Most CCA scenarios draw from one or two domains. "
            "Multi-agent research draws from the three heaviest simultaneously.\n\n"
            "| Domain | Weight | What It Tests Here |\n"
            "|--------|--------|--------------------|\n"
            "| Agentic Architecture & Orchestration | **27%** | "
            "Hub-and-spoke, task decomposition, parallel waves |\n"
            "| Tool Design & MCP Integration | **18%** | "
            "4-5 tools per agent, negative bounds, MCP primitives |\n"
            "| Context Management & Reliability | **15%** | "
            "Context isolation, structured errors, conflict resolution |\n"
            "| **Combined coverage** | **60%** | "
            "Every exam concept in this scenario maps to a question pattern |\n\n"
            "This means studying this one scenario deeply teaches you more than studying "
            "three separate scenarios that each cover one domain. The article this "
            "companion pairs with calls this scenario \"the one that separates strong "
            "candidates from average ones\" -- because the same candidate who can navigate "
            "multi-agent research almost always handles the other scenarios too.\n\n"
            "Each notebook demonstrates a CCA anti-pattern side-by-side with the correct "
            "architectural pattern, using runnable code you can experiment with."
        ),
        _md(
            "## Project Architecture at a Glance\n\n"
            "The codebase has two layers:\n\n"
            "1. **The Python package** (`src/research_agents/`) -- production implementation "
            "with correct patterns only\n"
            "2. **Anti-patterns** (`src/research_agents/anti_patterns/`) -- deliberately wrong "
            "implementations imported only by notebooks\n\n"
            "The coordinator follows a **6-step orchestration flow**:\n\n"
            "```\n"
            "Research query\n"
            "  -> 1. PLAN:      Decompose into SubTasks with depends_on fields\n"
            "  -> 2. SORT:      Topological sort into parallel execution waves\n"
            "  -> 3. DELEGATE:  Build explicit context -> run_agent_loop with scoped tools\n"
            "  -> 4. EVALUATE:  Send results to fact_checker for cross-referencing\n"
            "  -> 5. RESOLVE:   Deterministic conflict resolution (not LLM judgment)\n"
            "  -> 6. SYNTHESIZE: Compile ResearchReport with findings, conflicts, and gaps\n"
            "```\n\n"
            "All services are simulated in-memory -- no API key needed for these notebooks."
        ),
        _code("import sys\nprint(f'Python {sys.version}')"),
        _code("import research_agents\nprint(f'research_agents v{research_agents.__version__}')"),
        _code(
            "from research_agents.services.container import ServiceContainer\n"
            "from research_agents.data.sources import SEARCH_INDEX\n"
            "print(f'Search index has {len(SEARCH_INDEX)} keyword groups')"
        ),
        _code(
            "# Verify API key (only needed for live demos)\n"
            "import os\n"
            "key = os.environ.get('ANTHROPIC_API_KEY', '')\n"
            "if key and key != 'your-api-key-here':\n"
            "    print('[OK] ANTHROPIC_API_KEY is set')\n"
            "else:\n"
            "    print('[WARN] ANTHROPIC_API_KEY not set -- notebooks will use mock mode')",
            skip=True,
        ),
        _md(
            "## Setup Complete\n\n"
            "If all cells above ran without errors, you're ready to proceed to Notebook 01.\n\n"
            "### Notebook Index\n\n"
            "| # | Topic | CCA Domain |\n"
            "|---|-------|------------|\n"
            "| 01 | Hub-and-Spoke Architecture | Agentic Architecture (27%) |\n"
            "| 02 | Context Isolation | Context Management (15%) |\n"
            "| 03 | Tool Scoping | Tool Design & MCP (18%) |\n"
            "| 04 | Structured Error Handling | Reliability (15%) |\n"
            "| 05 | Task Decomposition | Agentic Architecture (27%) |\n"
            "| 06 | Conflict Resolution | Reliability (15%) |\n"
            "| 07 | MCP Primitives | Tool Design & MCP (18%) |\n"
            "| 08 | Integration | All three domains (60%) |"
        ),
    ])
    _save(nb, "00_setup.ipynb")


# ---- Notebook 01: Hub-and-Spoke Architecture ----

def gen_01():
    nb = _make_nb([
        _md(
            "# 01 --- Hub-and-Spoke Architecture\n\n"
            "**CCA Pattern**: The coordinator sits at the hub. Specialized subagents are the "
            "spokes. Spokes talk only to the hub, never to each other.\n\n"
            "This notebook demonstrates how the coordinator decomposes a research query into "
            "subtasks and delegates to specialized agents."
        ),
        _code(
            "import sys\nfrom pathlib import Path\n"
            "sys.path.insert(0, str(Path('..').resolve()))\n"
            "sys.path.insert(0, str(Path('.').resolve()))"
        ),
        _code(
            "from research_agents.models.research import SubTask\n"
            "from research_agents.agent.coordinator import sort_tasks_into_waves\n"
            "from research_agents.agent.subagents import SUBAGENT_CONFIGS\n"
            "from research_agents.tools.definitions import ALL_TOOL_SETS"
        ),
        _md(
            "## Understanding the Key Data Structures\n\n"
            "### SubTask -- The Unit of Delegation\n\n"
            "The `SubTask` model (from `models/research.py`) is the data structure the coordinator "
            "uses to delegate work. Each field maps to a CCA concept:\n\n"
            "```python\n"
            "class SubTask(BaseModel):\n"
            "    task_id: str           # Unique identifier for dependency tracking\n"
            "    agent_type: str        # Which specialized agent handles this\n"
            "    instruction: str       # What to do (the \"task\")\n"
            "    context: str           # ONLY what the coordinator chose to pass\n"
            "    depends_on: list[str]  # task_ids that must complete first\n"
            "```\n\n"
            "The critical field is `context`. It contains **only** what the coordinator explicitly "
            "selected -- not the coordinator's full conversation history. This is context isolation "
            "in data form. We'll explore this deeply in Notebook 02.\n\n"
            "### SubagentConfig -- System Prompt + Scoped Tools\n\n"
            "Each agent type has a frozen configuration in `agent/subagents.py`:\n\n"
            "```python\n"
            "@dataclass(frozen=True)\n"
            "class SubagentConfig:\n"
            "    system_prompt: str   # Agent-specific instructions\n"
            "    tools: list[dict]    # 4 scoped tools (never the full set)\n"
            "```\n\n"
            "The `frozen=True` means configs are immutable after creation. A web researcher "
            "always gets the same 4 tools -- the coordinator cannot accidentally give it "
            "fact-checking tools at runtime."
        ),
        _md(
            "## The Newsroom Analogy\n\n"
            "Think of the architecture as a newsroom:\n\n"
            "- **Coordinator = Editor.** Assigns stories, decides the front page, resolves "
            "disagreements between reporters.\n"
            "- **Subagents = Specialist reporters.** One covers business, one covers science, "
            "one fact-checks. Each has their own beat, their own contacts, their own tools.\n"
            "- **`SubTask` = Assignment slip.** Tells a reporter what to write, what angle "
            "the editor wants, and what background the reporter needs to get started.\n"
            "- **`ResearchReport` = The published story.** Combines all filed copy with "
            "editorial judgment about what's verified and what's still open.\n\n"
            "Reporters do not call each other mid-assignment. If the business reporter "
            "needs something from the science reporter, the editor brokers it. This is "
            "the hub-and-spoke shape -- and it is exactly why subagent-to-subagent "
            "communication is the wrong answer on the CCA exam."
        ),
        _md(
            "## Anti-Pattern: Subagent-to-Subagent Communication\n\n"
            "The most common distractor on the exam lets subagents talk directly. "
            "It looks efficient but it breaks the coordination contract. Pseudocode:\n\n"
            "```python\n"
            "# WRONG: subagent calls another subagent directly\n"
            "def run_web_researcher(task):\n"
            "    sources = search_web(task.query)\n"
            "    # Reach out sideways to the fact checker\n"
            "    verified = fact_checker_agent.verify(sources)   # no!\n"
            "    return verified\n"
            "```\n\n"
            "What breaks:\n\n"
            "- **No single point of coordination.** The editor no longer knows what was verified.\n"
            "- **Context leakage.** The fact checker inherits the web researcher's task context "
            "(violating the isolation rule from Notebook 02).\n"
            "- **Unpredictable ordering.** `sort_tasks_into_waves()` loses its meaning -- "
            "any subagent can trigger any other at any time.\n"
            "- **No conflict resolution.** When the web researcher and fact checker disagree, "
            "there is no hub to reconcile them (that is Notebook 06).\n\n"
            "In this codebase, `build_subagent_context()` is the **only** way a subagent "
            "receives input, and it takes a `SubTask` plus optional predecessor results -- "
            "never another subagent's client or session. Sideways communication is "
            "structurally impossible."
        ),
        _md("## Correct Pattern: Specialized Subagents\n\nEach agent has its own system prompt and 4 scoped tools."),
        _code(
            "# Show each agent's tool count and tool names\n"
            "for agent_type, config in SUBAGENT_CONFIGS.items():\n"
            "    tool_names = [t['name'] for t in config.tools]\n"
            "    print(f'{agent_type}: {len(config.tools)} tools')\n"
            "    print(f'  Tools: {\", \".join(tool_names)}')\n"
            "    print(f'  Prompt preview: {config.system_prompt[:80].strip()}...')\n"
            "    print()"
        ),
        _md(
            "### How the Coordinator Delegates\n\n"
            "The coordinator's 6-step flow starts with decomposing a query into `SubTask` objects, "
            "then topologically sorting them into **waves** based on `depends_on` fields:\n\n"
            "- **Wave 0**: Tasks with no dependencies (can run in parallel)\n"
            "- **Wave 1**: Tasks depending on wave-0 results (sequential)\n"
            "- **Wave N**: Tasks depending on wave-(N-1) results\n\n"
            "The `sort_tasks_into_waves()` function in `coordinator.py` implements this. "
            "Let's see it in action:"
        ),
        _code(
            "# Demonstrate task decomposition into parallel waves\n"
            "tasks = [\n"
            "    SubTask(task_id='t1', agent_type='web_researcher',\n"
            "        instruction='Search for renewable energy data',\n"
            "        context='Focus on 2024'),\n"
            "    SubTask(task_id='t2', agent_type='data_extractor',\n"
            "        instruction='Query capacity statistics',\n"
            "        context='renewable_capacity table'),\n"
            "    SubTask(task_id='t3', agent_type='fact_checker',\n"
            "        instruction='Verify claims',\n"
            "        context='', depends_on=['t1', 't2']),\n"
            "]\n"
            "waves = sort_tasks_into_waves(tasks)\n"
            "for i, wave in enumerate(waves):\n"
            "    task_ids = [t.task_id for t in wave]\n"
            "    print(f'Wave {i}: {task_ids} ({\", \".join(t.agent_type for t in wave)})')"
        ),
        _md(
            "Notice that `t1` (web_researcher) and `t2` (data_extractor) are in Wave 0 because "
            "they have no dependencies -- they can run in parallel. `t3` (fact_checker) depends "
            "on both, so it goes in Wave 1.\n\n"
            "### The ServiceContainer -- Dependency Injection\n\n"
            "All tool handlers receive a `ServiceContainer` rather than importing services directly:\n\n"
            "```python\n"
            "@dataclass(frozen=True)\n"
            "class ServiceContainer:\n"
            "    web_search: WebSearchService\n"
            "    document_store: DocumentStore\n"
            "    database: DatabaseService\n"
            "    knowledge_base: KnowledgeBase\n"
            "```\n\n"
            "The `frozen=True` makes the container immutable. This is dependency injection -- "
            "if you later replace `WebSearchService` with a real API client, only the container "
            "construction changes. Tool handlers are untouched."
        ),
        _md(
            "## CCA Exam Tip\n\n"
            "> When a CCA exam question asks about the correct architecture for a multi-agent system:\n"
            "> - **Look for** the option with a single coordinator delegating to specialized subagents\n"
            "> - **If an answer** describes subagents communicating directly with each other "
            "or sharing context automatically, that is the distractor\n"
            "> - The hub-and-spoke pattern keeps coordination centralized\n"
            "> - Each spoke (subagent) has its own system prompt, scoped tools, and "
            "receives only explicit context"
        ),
    ])
    _save(nb, "01_hub_and_spoke.ipynb")


# ---- Notebook 02: Context Isolation ----

def gen_02():
    nb = _make_nb([
        _md(
            "# 02 --- Context Isolation\n\n"
            "**CCA Pattern**: Subagents do NOT inherit coordinator context. Each starts blank "
            "-- it receives ONLY what was explicitly passed.\n\n"
            "This is the concept that trips up more candidates than any other."
        ),
        _code(
            "import sys\nfrom pathlib import Path\n"
            "sys.path.insert(0, str(Path('..').resolve()))\n"
            "sys.path.insert(0, str(Path('.').resolve()))"
        ),
        _code(
            "from research_agents.models.research import SubTask\n"
            "from research_agents.agent.context_builder import build_subagent_context\n"
            "from research_agents.agent.agent_loop import AgentResult"
        ),
        _md(
            "## How Context Isolation Works\n\n"
            "The `build_subagent_context()` function in `agent/context_builder.py` is the "
            "**only** way to create subagent input. It builds a plain string from three sources:\n\n"
            "1. **`task.instruction`** -- what to do (always present)\n"
            "2. **`task.context`** -- explicitly selected facts from the coordinator\n"
            "3. **Predecessor results** -- filtered to only `task.depends_on` task IDs\n\n"
            "What the subagent does **NOT** receive:\n"
            "- The coordinator's message history\n"
            "- The coordinator's system prompt\n"
            "- Other subagents' results (unless listed in `depends_on`)\n"
            "- The original research query (unless the coordinator chose to include it)\n\n"
            "This is **structural isolation** -- the function signature makes it impossible "
            "to accidentally leak coordinator state:\n\n"
            "```python\n"
            "def build_subagent_context(\n"
            "    task: SubTask,\n"
            "    predecessor_results: dict[str, AgentResult] | None = None,\n"
            ") -> str:\n"
            "```\n\n"
            "The coordinator's `messages` list is not even a parameter. You cannot pass it."
        ),
        _md(
            "## Worked Example: Why Subagents Return MLA When Told to Use APA\n\n"
            "This is the canonical CCA exam scenario for context isolation. Read it "
            "carefully before the anti-pattern cell below -- the sequence of events is "
            "exactly what the exam tests.\n\n"
            "**The setup:**\n\n"
            "1. A user asks the coordinator: *\"Research renewable energy adoption. Use "
            "APA citation format for all sources.\"*\n"
            "2. The coordinator reasons: \"I'll decompose this into web research, "
            "document analysis, and fact checking.\"\n"
            "3. The coordinator creates three `SubTask` objects. Each `SubTask.instruction` "
            "says \"Search for renewable energy data\" (or similar). **The APA formatting "
            "requirement never makes it into any `SubTask.context`.**\n"
            "4. The web researcher runs, does a fine job finding sources, and returns "
            "citations formatted in MLA because MLA is its statistical default.\n"
            "5. The user sees the final report, notices the citations are wrong, and "
            "reports it as a bug.\n\n"
            "**Why the exam calls this the most-missed pattern:** it looks like the "
            "subagent disobeyed the coordinator. It didn't. It never received the "
            "instruction. The APA requirement was in the coordinator's turn-1 message, "
            "which the subagent structurally cannot see. The instruction lived in a "
            "place the subagent has no access to.\n\n"
            "**The fix is explicit forwarding.** When the coordinator decomposes, "
            "anything that applies to all subagents (citation format, tone, date range, "
            "output schema) must be copied into every `SubTask.context` where it "
            "applies. No inheritance. No magic. Just explicit passing."
        ),
        _md("## Anti-Pattern: Shared Context\n\nThe coordinator passes its full message history to the subagent."),
        _code(
            "from research_agents.anti_patterns.shared_context import run_leaky_subagent\n\n"
            "# Simulate coordinator messages\n"
            "coordinator_messages = [\n"
            "    {'role': 'user', 'content': 'Research renewable energy globally'},\n"
            "    {'role': 'assistant', 'content': 'I will decompose this into subtasks...'},\n"
            "    {'role': 'user', 'content': 'Use APA citation format for all sources'},\n"
            "]\n\n"
            "# The leaky function converts messages to str() -- wasteful and polluting\n"
            "leaked_context = str(coordinator_messages)\n"
            "print(f'Leaked context length: {len(leaked_context)} chars')\n"
            "print(f'Contains APA instruction: {\"APA\" in leaked_context}')\n"
            "print(f'Contains coordinator reasoning: {\"decompose\" in leaked_context}')"
        ),
        _md(
            "### Why This Fails\n\n"
            "The `run_leaky_subagent()` function in `anti_patterns/shared_context.py` does this:\n\n"
            "```python\n"
            "leaked_context = str(coordinator_messages)  # WRONG\n"
            "```\n\n"
            "Problems:\n"
            "- **Token waste**: the subagent processes the entire coordinator conversation\n"
            "- **Context pollution**: a web researcher sees document analysis instructions\n"
            "- **Attention dilution**: useful context is buried in irrelevant messages\n"
            "- **No isolation**: the subagent sees other subagents' results"
        ),
        _md("## Correct Pattern: Explicit Context Passing\n\nThe context builder passes ONLY what the coordinator deliberately selects."),
        _code(
            "# Correct: SubTask contains only explicit context\n"
            "task = SubTask(\n"
            "    task_id='t1',\n"
            "    agent_type='web_researcher',\n"
            "    instruction='Search for renewable energy adoption statistics',\n"
            "    context='Focus on 2024 data from government and peer-reviewed sources. "
            "Use APA citation format.',\n"
            ")\n\n"
            "explicit_context = build_subagent_context(task)\n"
            "print(f'Explicit context length: {len(explicit_context)} chars')\n"
            "print(f'Contains instruction: {\"renewable energy\" in explicit_context}')\n"
            "print(f'Contains APA format: {\"APA\" in explicit_context}')\n"
            "print(f'Contains coordinator reasoning: {\"decompose\" in explicit_context}')\n"
            "print()\nprint(explicit_context)"
        ),
        _md(
            "### Predecessor Results: The `depends_on` Filter\n\n"
            "When a task depends on earlier tasks, the context builder includes only those "
            "specific results -- not all prior results:\n"
        ),
        _code(
            "# Simulate predecessor results from Wave 0\n"
            "prior_results = {\n"
            "    't1': AgentResult(content='Found 4 sources on renewable energy.'),\n"
            "    't2': AgentResult(content='Database shows 1580 GW solar capacity in 2024.'),\n"
            "    't3': AgentResult(content='Document analysis of IEA report complete.'),\n"
            "}\n\n"
            "# Fact checker depends on t1 and t2 only -- NOT t3\n"
            "fact_check_task = SubTask(\n"
            "    task_id='t4',\n"
            "    agent_type='fact_checker',\n"
            "    instruction='Verify renewable energy claims',\n"
            "    context='Cross-reference web and database findings',\n"
            "    depends_on=['t1', 't2'],  # Only these results are passed\n"
            ")\n\n"
            "context_with_deps = build_subagent_context(fact_check_task, prior_results)\n"
            "print(context_with_deps)\n"
            "print()\n"
            "print(f'Contains t1 result: {\"Found 4 sources\" in context_with_deps}')\n"
            "print(f'Contains t2 result: {\"1580 GW\" in context_with_deps}')\n"
            "print(f'Contains t3 result: {\"IEA report\" in context_with_deps}')  # Should be False"
        ),
        _code(
            "from helpers import compare_results\n\n"
            "compare_results(\n"
            "    {'context_length': len(leaked_context), "
            "'contains_coordinator_reasoning': True, "
            "'contains_other_agent_results': True, "
            "'type': 'str(messages)'},\n"
            "    {'context_length': len(explicit_context), "
            "'contains_coordinator_reasoning': False, "
            "'contains_other_agent_results': False, "
            "'type': 'explicit_string'},\n"
            ")"
        ),
        _md(
            "## CCA Exam Tip\n\n"
            "> Any question where a subagent produces results that 'should have followed the "
            "coordinator\\'s instructions' is testing context isolation.\n"
            "> - The answer is always that the instructions were in the coordinator's context "
            "but never explicitly forwarded\n"
            "> - Subagents do not inherit. Subagents receive only what you explicitly send.\n"
            "> - The `build_subagent_context()` pattern enforces this structurally -- "
            "the coordinator's messages are never a function parameter"
        ),
    ])
    _save(nb, "02_context_isolation.ipynb")


# ---- Notebook 03: Tool Scoping ----

def gen_03():
    nb = _make_nb([
        _md(
            "# 03 --- Tool Scoping: 4-5 Tools Per Agent\n\n"
            "**CCA Pattern**: Each agent gets 4-5 focused tools. The super agent anti-pattern "
            "(18+ tools) causes tool selection degradation.\n\n"
            "The exam's official guidance is specific: **keep 4-5 tools per agent**. "
            "This is the exam-correct answer."
        ),
        _code(
            "import sys\nfrom pathlib import Path\n"
            "sys.path.insert(0, str(Path('..').resolve()))\n"
            "sys.path.insert(0, str(Path('.').resolve()))"
        ),
        _code(
            "from research_agents.tools.definitions import ALL_TOOL_SETS\n"
            "from research_agents.anti_patterns.super_agent import SUPER_AGENT_TOOLS, get_super_agent_tool_count"
        ),
        _md(
            "## How Tool Definitions Work\n\n"
            "Tool definitions live in `tools/definitions.py`. Each agent type has a constant "
            "list of tool dicts, for example `WEB_RESEARCHER_TOOLS`.\n\n"
            "Each tool dict follows the Claude API format:\n\n"
            "```python\n"
            "{\n"
            "    \"name\": \"search_web\",\n"
            "    \"description\": (\n"
            "        \"Search the public web for information matching a query. \"\n"
            "        \"Returns URLs, titles, and snippets. \"\n"
            "        \"Does NOT fetch full page content (use fetch_page for that). \"\n"
            "        \"Does NOT search internal documents or databases.\"\n"
            "    ),\n"
            "    \"input_schema\": { ... }\n"
            "}\n"
            "```\n\n"
            "### Negative-Bound Descriptions\n\n"
            "Every tool description includes **\"Does NOT...\"** clauses. This is the CCA "
            "negative-bound pattern -- it tells Claude what a tool *cannot* do, preventing "
            "misrouting. Without these, Claude might call `search_web` when it needs "
            "`parse_document`, because both involve finding information.\n\n"
            "### The Dispatch Registry\n\n"
            "Tool handlers are dispatched via a nested dict in `tools/handlers.py`:\n\n"
            "```python\n"
            "DISPATCH: dict[str, dict[str, Handler]] = {\n"
            "    \"web_researcher\": {\n"
            "        \"search_web\": handle_search_web,\n"
            "        \"fetch_page\": handle_fetch_page,\n"
            "        ...\n"
            "    },\n"
            "    ...\n"
            "}\n"
            "```\n\n"
            "The key insight: dispatch is keyed by `(agent_type, tool_name)`. Even if two agents "
            "had a tool with the same name, they'd route to different handlers. Tools are isolated "
            "per agent at the dispatch level."
        ),
        _md("## Anti-Pattern: Super Agent with 18+ Tools"),
        _code(
            "# The super agent has ALL tools combined\n"
            "print(f'Super agent tool count: {get_super_agent_tool_count()}')\n"
            "print()\n"
            "print('All tools on one agent:')\n"
            "for i, tool in enumerate(SUPER_AGENT_TOOLS, 1):\n"
            "    print(f'  {i:2d}. {tool[\"name\"]:<25s} {tool[\"description\"][:60]}...')"
        ),
        _md(
            "### Why 18+ Tools Fails\n\n"
            "When an agent has 18 tools:\n"
            "- A significant portion of attention goes to evaluating tool descriptions "
            "instead of the actual task\n"
            "- Similar tools create ambiguity (e.g., `search_web` vs `cross_reference` -- "
            "both find information)\n"
            "- **Better descriptions don't fix the structural problem** -- this is a "
            "key exam distractor"
        ),
        _md(
            "## The Show Truck vs. Work Truck Analogy\n\n"
            "A useful mental model for the exam: imagine a mechanic arriving at a job site.\n\n"
            "- **The show truck** is magnificent. It carries *every tool the mechanic owns* -- "
            "18 drawers of sockets, 12 types of wrench, a dozen diagnostic computers, a "
            "lift and a press. Impressive. Also: every time the mechanic needs a 10mm "
            "socket, they search through 18 drawers. Every minute spent searching is a "
            "minute not spent working. The show truck looks capable but is *operationally* "
            "slow because selection cost dominates work cost.\n\n"
            "- **The work truck** carries exactly the 4-5 tools for today's job. The "
            "mechanic reaches without looking. No selection overhead. If tomorrow's job "
            "needs different tools, they swap the loadout -- they don't bolt on more "
            "drawers.\n\n"
            "Every specialized agent in this project is a work truck. The `super_agent` "
            "anti-pattern is a show truck. The CCA exam's correct answer is always "
            "\"give the mechanic the right work truck\" -- not \"improve the labels on "
            "the show truck's drawers.\"\n\n"
            "Concretely in this codebase: `WEB_RESEARCHER_TOOLS` is the web researcher's "
            "work truck. `DOCUMENT_ANALYZER_TOOLS` is the document analyzer's. Each set "
            "has exactly 4 tools. When the coordinator dispatches a task, it hands the "
            "*right* work truck to the *right* mechanic. That handoff is structural, "
            "not suggestive -- the dispatch registry in `tools/handlers.py` keys on "
            "`(agent_type, tool_name)`, so even if two trucks had a tool with the same "
            "name they'd route to different handlers."
        ),
        _md("## Correct Pattern: Focused Tool Sets"),
        _code(
            "# Each agent has 4 focused tools\n"
            "print('Focused tool sets:')\n"
            "for agent_type, tools in ALL_TOOL_SETS.items():\n"
            "    tool_names = [t['name'] for t in tools]\n"
            "    print(f'  {agent_type:<20s} ({len(tools)} tools): {\", \".join(tool_names)}')"
        ),
        _code(
            "from helpers import compare_results\n\n"
            "compare_results(\n"
            "    {'total_tools': get_super_agent_tool_count(), "
            "'tools_per_agent': get_super_agent_tool_count(), 'agents': 1},\n"
            "    {'total_tools': sum(len(t) for t in ALL_TOOL_SETS.values()), "
            "'tools_per_agent': 4, 'agents': len(ALL_TOOL_SETS)},\n"
            ")"
        ),
        _md(
            "## CCA Exam Tip\n\n"
            "> The super agent question is one of the most reliable on the CCA exam.\n"
            "> Answer choices will include:\n"
            "> - 'improve tool descriptions' -- WRONG\n"
            "> - 'add a tool-selection preprocessing step' -- WRONG\n"
            "> - **'decompose into specialized subagents with 4-5 tools each' -- CORRECT**\n"
            "> The improvement is architectural, not descriptive.\n\n"
            "*Why architectural?* The root cause is **attention fragmentation** -- "
            "an 18-tool menu dilutes the model's focus regardless of how well each "
            "tool is described. Sharper descriptions are a band-aid; fewer, scoped "
            "tools fix the mechanism."
        ),
    ])
    _save(nb, "03_tool_scoping.ipynb")


# ---- Notebook 04: Error Handling ----

def gen_04():
    nb = _make_nb([
        _md(
            "# 04 --- Structured Error Handling\n\n"
            "**CCA Pattern**: Subagents return structured error context so the coordinator can "
            "retry, flag gaps, or adjust confidence.\n\n"
            "**Anti-pattern**: Silent failures return `{\"status\":\"success\",\"data\":null}` "
            "-- the coordinator can't tell if the source was empty or failed."
        ),
        _code(
            "import sys, json\nfrom pathlib import Path\n"
            "sys.path.insert(0, str(Path('..').resolve()))\n"
            "sys.path.insert(0, str(Path('.').resolve()))"
        ),
        _code(
            "from research_agents.tools.handlers import dispatch\n"
            "from research_agents.anti_patterns.silent_failures import handle_fetch_page_silent\n"
            "from tests.conftest import make_services\n"
            "services = make_services()"
        ),
        _md(
            "## The ToolErrorResponse Model\n\n"
            "When a tool handler encounters an error, it returns a `ToolErrorResponse` "
            "(from `models/errors.py`):\n\n"
            "```python\n"
            "class ToolErrorResponse(BaseModel):\n"
            "    status: str = \"error\"\n"
            "    error_type: str    # \"timeout\", \"not_found\", \"rate_limit\", etc.\n"
            "    source: str        # which service/URL failed\n"
            "    message: str       # human-readable error description\n"
            "    retry_eligible: bool      # Can the coordinator retry?\n"
            "    fallback_available: bool   # Is there an alternative source?\n"
            "    partial_data: dict | None  # Any data recovered before failure\n"
            "```\n\n"
            "This gives the coordinator a **decision tree**:\n"
            "- `retry_eligible=True` -> retry (timeouts, rate limits)\n"
            "- `fallback_available=True` -> try alternative source\n"
            "- Both `False` -> flag gap in the final report\n\n"
            "### The Anti-Pattern: SilentFailureResponse\n\n"
            "```python\n"
            "class SilentFailureResponse(BaseModel):\n"
            "    status: str = \"success\"  # LIES\n"
            "    data: None = None         # No data, but claims success\n"
            "```\n\n"
            "The coordinator cannot distinguish between:\n"
            "- 'no relevant data exists' (legitimate empty result)\n"
            "- 'the subagent failed to retrieve data' (error needing handling)"
        ),
        _md(
            "## Simulated Data: Intentional Failures\n\n"
            "The project's test data (in `data/sources.py`) includes URLs that intentionally fail:\n\n"
            "| URL | Behavior | Purpose |\n"
            "|-----|----------|---------|\n"
            "| `timeout.example.com/remote-data` | Simulated timeout | Tests retry logic |\n"
            "| `healthtech.example.com/ai-revolution` | Simulated 404 | Tests fallback logic |\n\n"
            "Let's see how each handler responds to these failures."
        ),
        _md("## Anti-Pattern: Silent Failure"),
        _code(
            "# Silent failure on timeout -- returns success with null\n"
            "silent_result = json.loads(handle_fetch_page_silent(\n"
            "    {'url': 'https://timeout.example.com/remote-data'}, services\n"
            "))\n"
            "print('Silent failure response:')\n"
            "print(json.dumps(silent_result, indent=2))\n"
            "print(f'\\nCan coordinator tell this was a timeout? {\"error_type\" in silent_result}')"
        ),
        _md(
            "### Why This Fails: The Silent-Failure Cascade\n\n"
            "The response above is `{\"status\": \"success\", \"data\": null}` -- it looks "
            "identical to a legitimate empty result, and the coordinator has no way to tell "
            "them apart. That ambiguity is the whole problem. Now imagine a five-step "
            "research pipeline where step 2 is a web fetch that silently times out. "
            "Steps 3, 4, and 5 proceed on the empty payload as if it were ground truth. "
            "The coordinator synthesizes a `ResearchReport` with a plausible confidence "
            "score because nothing ever reported a failure. The missing source is invisible.\n\n"
            "A single silent failure high in the dependency graph *cascades*: every "
            "downstream task treats `null` as legitimate, the conflict resolver has no "
            "contradictions to weigh (because one of the disputing sources never arrived), "
            "and the final report declares no gaps. The user sees a confident-looking "
            "answer that is quietly incomplete. This is why the CCA exam's correct "
            "answer is always \"require structured error context\" rather than \"add retry "
            "logic\" -- retry is one branch of the decision tree, and you cannot build a "
            "decision tree on a response that refuses to admit failure."
        ),
        _md("## Correct Pattern: Structured Error Context"),
        _code(
            "# Structured error on timeout -- coordinator gets full decision tree\n"
            "structured_result = json.loads(dispatch(\n"
            "    'web_researcher', 'fetch_page',\n"
            "    {'url': 'https://timeout.example.com/remote-data'}, services\n"
            "))\n"
            "print('Structured error response:')\n"
            "print(json.dumps(structured_result, indent=2))\n"
            "print(f'\\nCan coordinator retry? {structured_result.get(\"retry_eligible\")}')\n"
            "print(f'Error type: {structured_result.get(\"error_type\")}')"
        ),
        _code(
            "# Also show a 404 error (different decision tree)\n"
            "not_found_result = json.loads(dispatch(\n"
            "    'web_researcher', 'fetch_page',\n"
            "    {'url': 'https://healthtech.example.com/ai-revolution'}, services\n"
            "))\n"
            "print('404 error response:')\n"
            "print(json.dumps(not_found_result, indent=2))\n"
            "print(f'\\nRetry eligible: {not_found_result.get(\"retry_eligible\")}')  # False\n"
            "print(f'Fallback available: {not_found_result.get(\"fallback_available\")}')  # True"
        ),
        _code(
            "from helpers import compare_results\n\n"
            "compare_results(\n"
            "    {'status': silent_result['status'], "
            "'has_error_type': 'error_type' in silent_result, "
            "'has_retry_eligible': 'retry_eligible' in silent_result, "
            "'coordinator_can_retry': False},\n"
            "    {'status': structured_result['status'], "
            "'has_error_type': 'error_type' in structured_result, "
            "'has_retry_eligible': 'retry_eligible' in structured_result, "
            "'coordinator_can_retry': structured_result.get('retry_eligible', False)},\n"
            ")"
        ),
        _md(
            "## CCA Exam Tip\n\n"
            "> The silent failure question presents a scenario where a report is missing data.\n"
            "> - 'increase timeout duration' -- WRONG (addresses symptoms, not root cause)\n"
            "> - 'add retry logic' -- WRONG (partially helpful but not the core fix)\n"
            "> - **'require structured error context from subagents' -- CORRECT**\n"
            ">\n"
            "> The key insight: the coordinator needs enough information to make a decision "
            "(retry, fallback, or flag gap). Silent failures remove that decision-making ability."
        ),
    ])
    _save(nb, "04_error_handling.ipynb")


# ---- Notebook 05: Task Decomposition ----

def gen_05():
    nb = _make_nb([
        _md(
            "# 05 --- Task Decomposition\n\n"
            "**CCA Pattern**: The coordinator decomposes queries into parallel and sequential "
            "phases based on data dependencies.\n\n"
            "Web search and document analysis can run in parallel. Fact checking depends on their "
            "results, so it runs after."
        ),
        _code(
            "import sys\nfrom pathlib import Path\n"
            "sys.path.insert(0, str(Path('..').resolve()))\n"
            "sys.path.insert(0, str(Path('.').resolve()))"
        ),
        _code(
            "from research_agents.models.research import SubTask\n"
            "from research_agents.agent.coordinator import sort_tasks_into_waves"
        ),
        _md(
            "## How `sort_tasks_into_waves()` Works\n\n"
            "The topological sort in `coordinator.py` is straightforward:\n\n"
            "```python\n"
            "def sort_tasks_into_waves(tasks: list[SubTask]) -> list[list[SubTask]]:\n"
            "    completed: set[str] = set()\n"
            "    remaining = list(tasks)\n"
            "    waves: list[list[SubTask]] = []\n"
            "    while remaining:\n"
            "        wave = [t for t in remaining\n"
            "                if all(d in completed for d in t.depends_on)]\n"
            "        # ... add wave, mark completed, continue\n"
            "    return waves\n"
            "```\n\n"
            "Each iteration finds all tasks whose dependencies are already completed. "
            "Those tasks form the next wave and can run in parallel. If no tasks can run "
            "(circular dependency), all remaining tasks are placed in one wave as a fallback.\n\n"
            "### The `depends_on` Field\n\n"
            "The `SubTask.depends_on` field is a list of `task_id` strings. This is the "
            "**only** mechanism that creates sequential ordering. Tasks with empty `depends_on` "
            "are independent and can run in parallel."
        ),
        _md(
            "## The Restaurant Kitchen Analogy\n\n"
            "Task decomposition on an exam looks abstract, but the kitchen version makes "
            "it obvious.\n\n"
            "A brigade kitchen has stations: appetizer, grill, pantry, pastry, and "
            "expediter. When an order comes in for a steak frites with a caesar salad:\n\n"
            "- The **grill** station cooks the steak and the fries can run in parallel "
            "at the fry station -- neither needs the other's output.\n"
            "- The **pantry** station builds the caesar salad in parallel with both of "
            "those -- independent inputs, independent tools.\n"
            "- The **expediter** plates everything -- and that step must wait for *all* "
            "stations to finish. The plating `depends_on` every upstream step.\n\n"
            "This is exactly what `sort_tasks_into_waves()` does. Independent stations "
            "(no `depends_on`) form Wave 0 and work simultaneously. The expediter, who "
            "needs everything, sits in Wave 1.\n\n"
            "Now picture a kitchen where *nothing* is parallelized -- the same cook has "
            "to finish the steak before the fries can start, and the fries before the "
            "salad. Every dish comes out cold. That is the sequential-only anti-pattern."
        ),
        _md(
            "## Anti-Pattern: Everything Sequential\n\n"
            "Forcing every task to `depends_on` its predecessor -- even when no data "
            "actually flows between them -- is the most common decomposition mistake "
            "on the exam. It runs correctly but wastes the coordinator's biggest "
            "available optimization. Here's what it looks like:"
        ),
        _code(
            "# ANTI-PATTERN: naive all-sequential decomposition\n"
            "# Web search does not need database stats to start.\n"
            "# Database stats do not need document analysis to start.\n"
            "# But the author chained them anyway.\n"
            "naive_tasks = [\n"
            "    SubTask(task_id='web', agent_type='web_researcher',\n"
            "        instruction='Search remote work studies', context=''),\n"
            "    SubTask(task_id='data', agent_type='data_extractor',\n"
            "        instruction='Query stats', context='',\n"
            "        depends_on=['web']),                  # not actually needed!\n"
            "    SubTask(task_id='docs', agent_type='document_analyzer',\n"
            "        instruction='Parse Stanford study', context='',\n"
            "        depends_on=['data']),                 # not actually needed!\n"
            "    SubTask(task_id='facts', agent_type='fact_checker',\n"
            "        instruction='Verify claims', context='',\n"
            "        depends_on=['web', 'docs']),          # legitimately dependent\n"
            "]\n"
            "naive_waves = sort_tasks_into_waves(naive_tasks)\n"
            "print(f'Anti-pattern wave count: {len(naive_waves)} "
            "(all single-task waves -- no parallelism)')\n"
            "for i, wave in enumerate(naive_waves):\n"
            "    print(f'  Wave {i}: {[t.task_id for t in wave]}')"
        ),
        _md(
            "### Why This Fails\n\n"
            "Nothing is *wrong* here -- the pipeline still produces the right result. "
            "It just takes 4x as long as it needs to. On the exam, any option that "
            "chains `depends_on` without an actual data dependency is the distractor. "
            "The CCA answer always asks: *does this task actually need the previous "
            "task's output?* If no, drop the `depends_on` edge.\n\n"
            "Below is the same research broken into the correct parallel + sequential "
            "shape. Compare the wave counts."
        ),
        _md("## Correct Pattern: Parallel + Sequential Waves"),
        _code(
            "# Define tasks with data dependencies\n"
            "tasks = [\n"
            "    SubTask(task_id='web', agent_type='web_researcher',\n"
            "        instruction='Search for remote work studies',\n"
            "        context='Focus on 2024'),\n"
            "    SubTask(task_id='data', agent_type='data_extractor',\n"
            "        instruction='Query remote work statistics',\n"
            "        context='remote_work_stats table'),\n"
            "    SubTask(task_id='docs', agent_type='document_analyzer',\n"
            "        instruction='Parse Stanford study',\n"
            "        context='doc-remote-work-stanford'),\n"
            "    SubTask(task_id='facts', agent_type='fact_checker',\n"
            "        instruction='Verify claims',\n"
            "        context='', depends_on=['web', 'data', 'docs']),\n"
            "]\n\n"
            "waves = sort_tasks_into_waves(tasks)\n"
            "for i, wave in enumerate(waves):\n"
            "    ids = [t.task_id for t in wave]\n"
            "    agents = [t.agent_type for t in wave]\n"
            "    print(f'Wave {i}: {ids}')\n"
            "    print(f'  Agents: {agents}')\n"
            "    print(f'  Can run in parallel: {len(wave) > 1}')\n"
            "    print()"
        ),
        _md(
            "### How the Coordinator Executes Waves\n\n"
            "In `run_coordinator()`, each wave is processed sequentially, but tasks within "
            "a wave could be parallelized:\n\n"
            "```python\n"
            "for wave in waves:\n"
            "    for task in wave:  # Could be concurrent\n"
            "        context_string = build_subagent_context(task, results)\n"
            "        result = run_agent_loop(client, services, context_string, ...)\n"
            "        results[task.task_id] = result\n"
            "```\n\n"
            "The current implementation processes tasks within a wave sequentially for "
            "simplicity, but the wave structure makes it trivial to add concurrency later. "
            "The key point for the CCA exam is that the **dependency analysis is correct** -- "
            "tasks that can run in parallel are identified."
        ),
        _code(
            "# Compare: all sequential (no parallelism)\n"
            "sequential_tasks = [\n"
            "    SubTask(task_id='web', agent_type='web_researcher',\n"
            "        instruction='a', context=''),\n"
            "    SubTask(task_id='data', agent_type='data_extractor',\n"
            "        instruction='b', context='', depends_on=['web']),\n"
            "    SubTask(task_id='docs', agent_type='document_analyzer',\n"
            "        instruction='c', context='', depends_on=['data']),\n"
            "    SubTask(task_id='facts', agent_type='fact_checker',\n"
            "        instruction='d', context='', depends_on=['docs']),\n"
            "]\n"
            "seq_waves = sort_tasks_into_waves(sequential_tasks)\n"
            "print(f'Parallel waves: {len(waves)} (wave 0 has {len(waves[0])} tasks)')\n"
            "print(f'Sequential waves: {len(seq_waves)} (all single-task waves)')"
        ),
        _md(
            "## CCA Exam Tip\n\n"
            "> Task decomposition questions ask whether two subtasks should run in parallel "
            "or sequentially.\n"
            "> - If Subtask B needs output from Subtask A -> sequential (`depends_on`)\n"
            "> - If they work from independent inputs -> parallel (no `depends_on`)\n"
            "> - 'Web search' and 'document parsing' are the canonical parallel pair\n"
            "> - 'Fact checking' and 'report writing' are always sequential\n"
            "> - The `SubTask.depends_on` field is the mechanism that creates ordering"
        ),
    ])
    _save(nb, "05_task_decomposition.ipynb")


# ---- Notebook 06: Conflict Resolution ----

def gen_06():
    nb = _make_nb([
        _md(
            "# 06 --- Conflict Resolution\n\n"
            "**CCA Pattern**: The coordinator resolves contradictions using deterministic strategies:\n"
            "1. Source reliability ranking\n"
            "2. Majority consensus\n"
            "3. Flag for human review\n\n"
            "This is programmatic enforcement -- not LLM judgment."
        ),
        _code(
            "import sys\nfrom pathlib import Path\n"
            "sys.path.insert(0, str(Path('..').resolve()))\n"
            "sys.path.insert(0, str(Path('.').resolve()))"
        ),
        _code(
            "from research_agents.agent.conflict_resolver import (\n"
            "    resolve_conflict, resolve_conflicts, RELIABILITY_SCORES\n"
            ")\n"
            "from research_agents.models.research import SourceReliability, ConflictRecord"
        ),
        _md(
            "## How the Conflict Resolver Works\n\n"
            "The `conflict_resolver.py` module uses **deterministic strategies** -- no LLM "
            "reasoning at all. This is the CCA principle that programmatic enforcement beats "
            "prompt-based guidance.\n\n"
            "### The ConflictRecord Model\n\n"
            "```python\n"
            "class ConflictRecord(BaseModel):\n"
            "    claim: str                 # The disputed factual claim\n"
            "    sources_for: list[str]     # URLs supporting the claim\n"
            "    sources_against: list[str] # URLs contradicting the claim\n"
            "    resolution: str            # \"majority\", \"highest_reliability\", \"flagged_for_human\"\n"
            "    confidence: float          # 0.0 to 1.0\n"
            "```\n\n"
            "### Reliability Scoring\n\n"
            "Sources are scored by reliability tier:\n\n"
            "| Tier | Score | Examples |\n"
            "|------|-------|---------|\n"
            "| HIGH | 3 | `.gov`, peer-reviewed journals, official statistics |\n"
            "| MEDIUM | 2 | Established news outlets, `.edu`, consultancies |\n"
            "| LOW | 1 | Blogs, unverified sources |\n"
            "| UNKNOWN | 0 | Not yet assessed |\n\n"
            "### Three-Tier Resolution Strategy\n\n"
            "1. **Reliability ranking**: Sum reliability scores for each side. Higher total wins. "
            "Confidence scales with the score difference.\n"
            "2. **Majority consensus**: If reliability ties, the side with more sources wins. "
            "Confidence = majority_size / total.\n"
            "3. **Human review**: If both reliability and count tie, flag for human review "
            "with low confidence (0.3)."
        ),
        _md("## Strategy 1: Source Reliability Ranking"),
        _code(
            "# Show the scoring constants\n"
            "print('Reliability scores:')\n"
            "for tier, score in RELIABILITY_SCORES.items():\n"
            "    print(f'  {tier.value:<10s} = {score}')\n"
            "print()\n\n"
            "# High-reliability source beats low-reliability\n"
            "reliability = {\n"
            "    'https://energy.gov/renewable-2024': SourceReliability.HIGH,\n"
            "    'https://energyblog.example.com/renewables': SourceReliability.LOW,\n"
            "}\n"
            "record = resolve_conflict(\n"
            "    claim='Renewable energy accounts for 30% of global electricity',\n"
            "    sources_for=['https://energy.gov/renewable-2024'],\n"
            "    sources_against=['https://energyblog.example.com/renewables'],\n"
            "    reliability_lookup=reliability,\n"
            ")\n"
            "print(f'Claim: {record.claim}')\n"
            "print(f'Resolution: {record.resolution}')\n"
            "print(f'Confidence: {record.confidence:.2f}')"
        ),
        _md(
            "## Strategy 2: Majority Vote (when reliabilities tie)\n\n"
            "If the reliability-summed scores come out equal on both sides, the resolver "
            "falls through to a majority vote. This matters in the most common real-world "
            "case: several moderately-reliable news outlets disagreeing with each other. "
            "No one side has a clear reliability edge, but three sources saying the same "
            "thing is stronger evidence than one source saying the opposite.\n\n"
            "The confidence on a majority resolution is `majority_count / total_count`. "
            "So 3 of 4 sources agreeing yields `0.75`. This is deliberately lower than "
            "the confidence ceiling on reliability wins (`0.95`) -- a reliability-based "
            "answer is treated as stronger evidence than a count-based answer, which "
            "is what you'd want on the exam."
        ),
        _code(
            "# Three medium-reliability sources for the claim, one against\n"
            "reliability_majority = {\n"
            "    'https://reuters.com/article-a': SourceReliability.MEDIUM,\n"
            "    'https://bbc.com/article-b': SourceReliability.MEDIUM,\n"
            "    'https://apnews.com/article-c': SourceReliability.MEDIUM,\n"
            "    'https://nytimes.com/article-d': SourceReliability.MEDIUM,\n"
            "}\n"
            "majority_record = resolve_conflict(\n"
            "    claim='Hybrid work arrangements increase employee retention',\n"
            "    sources_for=[\n"
            "        'https://reuters.com/article-a',\n"
            "        'https://bbc.com/article-b',\n"
            "        'https://apnews.com/article-c',\n"
            "    ],\n"
            "    sources_against=['https://nytimes.com/article-d'],\n"
            "    reliability_lookup=reliability_majority,\n"
            ")\n"
            "print(f'Resolution: {majority_record.resolution}')\n"
            "print(f'Confidence: {majority_record.confidence:.2f}  "
            "# 3 of 4 sources agree = 0.75')\n"
            "print(f'Sources for: {len(majority_record.sources_for)}, "
            "against: {len(majority_record.sources_against)}')"
        ),
        _md("## Strategy 3: Equal Reliability + Equal Count -> Human Review"),
        _code(
            "# Equal reliability + equal count -> human review\n"
            "reliability_equal = {\n"
            "    'https://reuters.com': SourceReliability.MEDIUM,\n"
            "    'https://bbc.com': SourceReliability.MEDIUM,\n"
            "}\n"
            "record2 = resolve_conflict(\n"
            "    claim='Remote work productivity',\n"
            "    sources_for=['https://reuters.com'],\n"
            "    sources_against=['https://bbc.com'],\n"
            "    reliability_lookup=reliability_equal,\n"
            ")\n"
            "print(f'Resolution: {record2.resolution}')\n"
            "print(f'Confidence: {record2.confidence:.2f}')"
        ),
        _md(
            "### How This Connects to the ResearchReport\n\n"
            "The `build_research_report()` function in `coordinator.py` uses conflict records "
            "to adjust the report's overall confidence score:\n\n"
            "```python\n"
            "base_confidence = 0.8\n"
            "if gaps:\n"
            "    base_confidence -= 0.1 * len(gaps)     # Each gap reduces confidence\n"
            "if conflict_records:\n"
            "    flagged = [c for c in conflict_records\n"
            "               if c.resolution == \"flagged_for_human\"]\n"
            "    base_confidence -= 0.05 * len(flagged)  # Unresolved conflicts reduce confidence\n"
            "```\n\n"
            "Reports that say 'we could not reach Source X' or 'these sources disagree and we "
            "flagged it for human review' are **more trustworthy** than reports that silently "
            "omit unavailable sources or pick the first result."
        ),
        _md(
            "## CCA Exam Tip\n\n"
            "> The conflict resolution question tests whether you understand that:\n"
            "> - Source reliability ranking is the first strategy\n"
            "> - Majority consensus applies when reliability is tied\n"
            "> - Human review is the fallback, not auto-resolution\n"
            "> - 'First result wins' is always the wrong answer\n"
            "> - The resolution is **deterministic** -- same inputs always produce same output\n\n"
            "*Why deterministic?* Enterprise systems need **predictable, auditable, "
            "repeatable** outcomes -- a resolution must be reviewable after the fact "
            "and reproducible for compliance. LLM judgment cannot meet those three "
            "requirements; programmatic rules can."
        ),
    ])
    _save(nb, "06_conflict_resolution.ipynb")


# ---- Notebook 07: MCP Primitives ----

def gen_07():
    nb = _make_nb([
        _md(
            "# 07 --- MCP Primitives\n\n"
            "**CCA Pattern**: MCP (Model Context Protocol) defines three primitives:\n"
            "- **Tools** -- executable functions an agent can invoke (verbs)\n"
            "- **Resources** -- data schemas and catalogs agents can query (nouns)\n"
            "- **Prompts** -- templates for common operations (patterns)\n\n"
            "The exam tests whether you know the difference."
        ),
        _code(
            "import sys\nfrom pathlib import Path\n"
            "sys.path.insert(0, str(Path('..').resolve()))\n"
            "sys.path.insert(0, str(Path('.').resolve()))"
        ),
        _code(
            "from research_agents.tools.definitions import ALL_TOOL_SETS"
        ),
        _md(
            "## Understanding the Three MCP Primitives\n\n"
            "MCP is a protocol that standardizes how AI agents interact with external systems. "
            "The CCA exam tests your ability to classify capabilities into the correct primitive.\n\n"
            "### The Key Distinction\n\n"
            "| Primitive | Nature | Analogy | Example |\n"
            "|-----------|--------|---------|--------|\n"
            "| **Tool** | Action (verb) | Function call | `verify_claim(claim)` |\n"
            "| **Resource** | Data (noun) | Database query | Source reliability ratings |\n"
            "| **Prompt** | Template (pattern) | Reusable format | Research query decomposition |\n\n"
            "The most common exam mistake is classifying a **Resource** as a **Tool**. "
            "A source reliability database is *data the agent reads* (Resource), not "
            "*an action the agent performs* (Tool).\n\n"
            "### How Our System Maps to MCP\n\n"
            "Our project uses the `anthropic` SDK directly (not the Agent SDK), so MCP primitives "
            "are represented as plain Python constructs. Here's how each maps:"
        ),
        _md("## Tools (Verbs) -- Things the Agent Does"),
        _code(
            "# Our tool definitions are MCP Tools -- executable functions\n"
            "for agent_type, tools in ALL_TOOL_SETS.items():\n"
            "    print(f'{agent_type}:')\n"
            "    for tool in tools:\n"
            "        print(f'  Tool: {tool[\"name\"]:<25s} (action/verb)')"
        ),
        _md(
            "Each tool above is an **action** the agent can invoke. `search_web` performs a search. "
            "`verify_claim` checks a claim. `delegate_task` triggers delegation. These are verbs.\n\n"
            "In MCP terms, each tool definition has:\n"
            "- A `name` (the function to call)\n"
            "- A `description` (what it does and does NOT do)\n"
            "- An `input_schema` (the parameters it accepts)"
        ),
        _md(
            "## Resources (Nouns) -- Things the Agent Reads\n\n"
            "In our system, these would be exposed as MCP Resources if we used the MCP protocol:"
        ),
        _code(
            "# Resources in our system (conceptual mapping)\n"
            "resources = {\n"
            "    'document_catalog': 'List of available research documents and their metadata',\n"
            "    'source_reliability_db': 'Database of source URLs and their reliability ratings',\n"
            "    'database_schemas': 'Schemas for available statistical tables',\n"
            "}\n"
            "for name, desc in resources.items():\n"
            "    print(f'  Resource: {name:<25s} (data/noun)')"
        ),
        _md(
            "These are **data** the agent queries, not actions it performs. In our codebase:\n\n"
            "- `source_reliability_db` -> `KnowledgeBase.get_source_reliability()` "
            "returns a SourceReliability enum\n"
            "- `document_catalog` -> `DocumentStore.list_documents()` returns document metadata\n"
            "- `database_schemas` -> `DatabaseService.get_schema()` returns column definitions\n\n"
            "In a full MCP implementation, these would be exposed as `resource://` URIs "
            "that agents can read without executing side effects."
        ),
        _md("## Prompts (Patterns) -- Templates the Agent Uses"),
        _code(
            "# Prompts in our system (conceptual mapping)\n"
            "prompts = {\n"
            "    'research_query_template': 'Template for decomposing a query into subtasks',\n"
            "    'citation_format_template': 'Template for formatting citations (APA)',\n"
            "    'error_report_template': 'Template for reporting structured errors',\n"
            "}\n"
            "for name, desc in prompts.items():\n"
            "    print(f'  Prompt: {name:<30s} (template/pattern)')"
        ),
        _md(
            "In our codebase, these map to:\n\n"
            "- `research_query_template` -> The system prompts in `subagents.py` "
            "(e.g., `WEB_RESEARCHER_PROMPT`)\n"
            "- `citation_format_template` -> Would be an MCP Prompt if we needed "
            "configurable citation styles\n"
            "- `error_report_template` -> The `ToolErrorResponse` model structure\n\n"
            "In MCP, Prompts are reusable templates that can be invoked with parameters. "
            "They're not system prompts -- they're parameterized message templates "
            "that standardize common operations."
        ),
        _md(
            "## Classification Exercise\n\n"
            "Five items below. For each, decide whether it is a **Tool**, a **Resource**, "
            "or a **Prompt** *before* reading the worked answer in the cell that follows. "
            "The CCA exam rewards snap classification, so practice making the call first."
        ),
        _md(
            "### Item 1 -- `verify_claim(claim: str) -> VerificationResult`\n\n"
            "Your classification?\n\n"
            "<details>\n<summary>Reveal the answer</summary>\n\n"
            "**Tool.** It performs an action: checking a claim against the knowledge base. "
            "It has side effects (it consumes a `claim` input and produces a "
            "`VerificationResult`). Anything shaped like a function call with an imperative "
            "verb in the name is almost always a Tool.\n\n"
            "Trap to avoid: candidates sometimes classify it as a Resource because it "
            "\"returns information.\" Tools also return information -- the distinguishing "
            "feature is *computation*, not read-only access.\n\n</details>"
        ),
        _md(
            "### Item 2 -- A database of source URLs with reliability ratings\n\n"
            "Your classification?\n\n"
            "<details>\n<summary>Reveal the answer</summary>\n\n"
            "**Resource.** It is read-only data the agent queries. In MCP, this would be "
            "exposed as a `resource://source-reliability` URI and the agent would *read* "
            "from it rather than *call* it.\n\n"
            "This is **the** canonical exam trap. Options include "
            "`get_source_reliability(url)` (a Tool-like wrapper) as a distractor. The "
            "underlying capability is a Resource even if the access pattern looks "
            "Tool-shaped. The exam question is usually worded in terms of the data "
            "itself (\"a database of ratings\"), which is the tell.\n\n</details>"
        ),
        _md(
            "### Item 3 -- A template for decomposing a research query into SubTasks\n\n"
            "Your classification?\n\n"
            "<details>\n<summary>Reveal the answer</summary>\n\n"
            "**Prompt.** It is a reusable pattern, parameterized by the incoming query, "
            "that produces a structured decomposition. Prompts in MCP are not system "
            "prompts -- they are *parameterized message templates* agents can invoke to "
            "standardize common operations.\n\n"
            "If you said \"Tool\" because it produces an output: Prompts also produce "
            "outputs. The distinguishing feature of a Prompt is that it is a "
            "*template* with named parameters, not a function with computation.\n\n</details>"
        ),
        _md(
            "### Item 4 -- `fetch_page(url: str) -> PageContent`\n\n"
            "Your classification?\n\n"
            "<details>\n<summary>Reveal the answer</summary>\n\n"
            "**Tool.** It performs the action of fetching a page and has observable side "
            "effects (network call, possible failure modes). This is the easiest kind of "
            "item on the exam -- clear verb, clear parameter, clear return type. If it "
            "can time out or fail, it is almost certainly a Tool (Resources are usually "
            "read-only and cacheable in a way that fetch calls are not).\n\n</details>"
        ),
        _md(
            "### Item 5 -- A catalog listing available research documents with metadata\n\n"
            "Your classification?\n\n"
            "<details>\n<summary>Reveal the answer</summary>\n\n"
            "**Resource.** A catalog is data the agent browses. The items in it may be "
            "things the agent can act on, but the catalog *itself* is a Resource.\n\n"
            "Watch this distinction on the exam: `list_documents()` is often listed as a "
            "Tool, but the underlying \"available documents\" is the Resource. If the "
            "question asks about the *capability*, go Resource. If it asks about the "
            "*function exposed to the agent*, the answer might be Tool. Read carefully.\n\n</details>"
        ),
        _md(
            "## CCA Exam Tip\n\n"
            "> The MCP primitives question is a vocabulary test:\n"
            "> - **Tools** are things the agent *does* (verbs)\n"
            "> - **Resources** are things the agent *reads* (nouns)\n"
            "> - **Prompts** are templates the agent *uses* (patterns)\n"
            ">\n"
            "> If a question describes a source reliability database -> **Resource**, not a Tool.\n"
            "> If it describes a function that verifies a claim -> **Tool**.\n"
            "> If it describes a reusable template for formatting citations -> **Prompt**.\n"
            ">\n"
            "> The most common distractor makes a Resource look like a Tool because "
            "both involve 'getting information.' The difference: Tools have **side effects** "
            "or perform **computation**; Resources are **read-only data**.\n\n"
            "*Foolproof test:* **if you cannot *run* it, it is probably a Resource.** "
            "A Tool *performs an action* (e.g., `fetch_page(url)`, `verify_claim(claim)`) "
            "-- often *using* a Resource. A Resource is the *data or infrastructure the "
            "Tool acts upon* (e.g., a database of sources, a schema catalog, a file "
            "system). Same information can appear behind either primitive -- ask which "
            "side of the verb it sits on."
        ),
    ])
    _save(nb, "07_mcp_primitives.ipynb")


# ---- Notebook 08: Integration ----

def gen_08():
    nb = _make_nb([
        _md(
            "# 08 --- Integration: Full End-to-End Research Query\n\n"
            "This notebook brings together all CCA patterns:\n"
            "- Hub-and-spoke coordinator\n"
            "- Context isolation via explicit passing\n"
            "- 4-5 scoped tools per agent\n"
            "- Structured error handling\n"
            "- Parallel + sequential task waves\n"
            "- Deterministic conflict resolution\n\n"
            "We'll walk through a complete research query using the `economic_impact` scenario."
        ),
        _code(
            "import sys, json\nfrom pathlib import Path\n"
            "sys.path.insert(0, str(Path('..').resolve()))\n"
            "sys.path.insert(0, str(Path('.').resolve()))"
        ),
        _code(
            "from research_agents.models.research import SubTask, ResearchReport\n"
            "from research_agents.agent.coordinator import (\n"
            "    sort_tasks_into_waves, run_coordinator, build_research_report\n"
            ")\n"
            "from research_agents.agent.context_builder import build_subagent_context\n"
            "from research_agents.agent.subagents import SUBAGENT_CONFIGS\n"
            "from research_agents.data.scenarios import SCENARIOS, ResearchScenario\n"
            "from research_agents.data.sources import SOURCE_RELIABILITY_RATINGS\n"
            "from research_agents.models.research import SourceReliability\n"
            "from tests.conftest import make_services"
        ),
        _md(
            "## The ResearchScenario Model\n\n"
            "The project defines pre-built scenarios (in `data/scenarios.py`) that combine "
            "all the patterns we've studied:\n\n"
            "```python\n"
            "@dataclass(frozen=True)\n"
            "class ResearchScenario:\n"
            "    name: str\n"
            "    query: str\n"
            "    expected_agents: list[str]  # Which agent types should be involved\n"
            "    expected_conflicts: int     # How many source contradictions\n"
            "    expected_gaps: int          # How many sources will fail\n"
            "    description: str\n"
            "```\n\n"
            "Three scenarios, each targeting different patterns:\n\n"
            "| Scenario | Tests | Conflicts | Gaps |\n"
            "|----------|-------|-----------|------|\n"
            "| `climate_renewable` | Conflict resolution | 1 (blog vs .gov) | 0 |\n"
            "| `ai_healthcare` | Error handling | 0 | 1 (404) |\n"
            "| `economic_impact` | Both | 1 (+13% vs -20%) | 1 (timeout) |"
        ),
        _md("## Scenario: Remote Work Economic Impact\n\nThis scenario tests both conflict resolution AND error handling."),
        _code(
            "scenario = SCENARIOS['economic_impact']\n"
            "print(f'Query: {scenario.query}')\n"
            "print(f'Expected agents: {scenario.expected_agents}')\n"
            "print(f'Expected conflicts: {scenario.expected_conflicts}')\n"
            "print(f'Expected gaps: {scenario.expected_gaps}')\n"
            "print(f'Description: {scenario.description}')"
        ),
        _md(
            "## Step 1: Task Decomposition (PLAN + SORT)\n\n"
            "The coordinator decomposes the query into SubTasks. In production, the LLM does "
            "this. Here we define them explicitly to show the structure:"
        ),
        _code(
            "# Decompose into subtasks (normally the LLM does this)\n"
            "tasks = [\n"
            "    SubTask(task_id='web', agent_type='web_researcher',\n"
            "        instruction='Search for studies on remote work and productivity',\n"
            "        context='Focus on 2024 data. Look for both pro and con evidence.'),\n"
            "    SubTask(task_id='data', agent_type='data_extractor',\n"
            "        instruction='Query remote work statistics from the database',\n"
            "        context='Use the remote_work_stats table'),\n"
            "    SubTask(task_id='docs', agent_type='document_analyzer',\n"
            "        instruction='Analyze the Stanford remote work study',\n"
            "        context='Document ID: doc-remote-work-stanford'),\n"
            "    SubTask(task_id='facts', agent_type='fact_checker',\n"
            "        instruction='Verify productivity claims from web and document sources',\n"
            "        context='Check claims about remote work productivity impact',\n"
            "        depends_on=['web', 'docs']),\n"
            "]\n\n"
            "waves = sort_tasks_into_waves(tasks)\n"
            "for i, wave in enumerate(waves):\n"
            "    print(f'Wave {i}: {[t.task_id for t in wave]} "
            "({\"parallel\" if len(wave) > 1 else \"sequential\"})' )"
        ),
        _md(
            "## Step 2: Context Isolation Check (DELEGATE)\n\n"
            "Each subagent gets ONLY its explicit context. Let's verify:"
        ),
        _code(
            "for task in tasks:\n"
            "    ctx = build_subagent_context(task)\n"
            "    print(f'{task.task_id} ({task.agent_type}):')\n"
            "    print(f'  Context length: {len(ctx)} chars')\n"
            "    print(f'  First 100 chars: {ctx[:100]}...')\n"
            "    print()"
        ),
        _md(
            "## Step 3: Run Coordinator (Mock Mode)\n\n"
            "Using a mock client for reproducible results. The `run_coordinator()` function "
            "executes Steps 2-3 of the 6-step flow:\n\n"
            "```python\n"
            "def run_coordinator(client, services, tasks, model) -> tuple[dict, list]:\n"
            "    waves = sort_tasks_into_waves(tasks)\n"
            "    for wave in waves:\n"
            "        for task in wave:\n"
            "            config = SUBAGENT_CONFIGS[task.agent_type]\n"
            "            context = build_subagent_context(task, results)\n"
            "            result = run_agent_loop(client, services, context, ...)\n"
            "            results[task.task_id] = result\n"
            "    return results, waves\n"
            "```"
        ),
        _code(
            "from types import SimpleNamespace\n\n"
            "call_count = 0\n"
            "def mock_create(**kwargs):\n"
            "    global call_count\n"
            "    call_count += 1\n"
            "    agent_responses = {\n"
            "        1: 'Found 4 sources. McKinsey reports +13% productivity. Blog claims -20%.',\n"
            "        2: 'Remote work stats: 9.4% fully remote, 18.2% hybrid in 2024.',\n"
            "        3: 'Stanford study: hybrid workers 13% more productive, 24% higher satisfaction.',\n"
            "        4: 'Verified: +13% claim supported by multiple sources. -20% claim unsupported.',\n"
            "    }\n"
            "    text = agent_responses.get(call_count, 'Analysis complete.')\n"
            "    return SimpleNamespace(\n"
            "        content=[SimpleNamespace(type='text', text=text)],\n"
            "        stop_reason='end_turn',\n"
            "        usage=SimpleNamespace(input_tokens=500, output_tokens=200),\n"
            "    )\n\n"
            "mock_client = SimpleNamespace(messages=SimpleNamespace(create=mock_create))\n"
            "services = make_services()\n\n"
            "results, waves = run_coordinator(mock_client, services, tasks)\n"
            "for task_id, result in results.items():\n"
            "    print(f'{task_id}: {result.content[:80]}...' "
            "if len(result.content) > 80 else f'{task_id}: {result.content}')"
        ),
        _md(
            "## Step 4: Conflict Resolution + Report (RESOLVE + SYNTHESIZE)\n\n"
            "The `build_research_report()` function compiles findings, resolves conflicts, "
            "and produces a `ResearchReport`:\n\n"
            "```python\n"
            "class ResearchReport(BaseModel):\n"
            "    query: str\n"
            "    findings: list[SourceResult]       # What we found\n"
            "    conflicts: list[ConflictRecord]     # What contradicted\n"
            "    synthesis: str                      # Combined narrative\n"
            "    confidence_score: float             # 0.0-1.0, adjusted by gaps/conflicts\n"
            "    gaps: list[str]                     # What we couldn't reach\n"
            "```\n\n"
            "The `gaps` field is critical -- a report that says 'we could not reach Source X' "
            "is more trustworthy than one that silently omits it."
        ),
        _code(
            "# Build report with conflict resolution\n"
            "conflicts = [{\n"
            "    'claim': 'Remote workers are more productive',\n"
            "    'sources_for': ['https://mckinsey.com/future-of-work', "
            "'https://bls.gov/remote-work-stats'],\n"
            "    'sources_against': ['https://workfromhome-blog.example.com/productivity'],\n"
            "}]\n\n"
            "reliability = {url: rel for url, rel in SOURCE_RELIABILITY_RATINGS.items()}\n\n"
            "report = build_research_report(\n"
            "    query=scenario.query,\n"
            "    results=results,\n"
            "    reliability_lookup=reliability,\n"
            "    conflicts=conflicts,\n"
            "    gaps=['https://timeout.example.com/remote-data (timeout)'],\n"
            ")\n\n"
            "print(f'Query: {report.query}')\n"
            "print(f'Findings: {len(report.findings)}')\n"
            "print(f'Conflicts resolved: {len(report.conflicts)}')\n"
            "for c in report.conflicts:\n"
            "    print(f'  - {c.claim}: {c.resolution} (confidence: {c.confidence:.2f})')\n"
            "print(f'Gaps: {report.gaps}')\n"
            "print(f'Confidence score: {report.confidence_score:.2f}')"
        ),
        _md(
            "## How the Pieces Connect\n\n"
            "Here's the complete data flow we just executed:\n\n"
            "```\n"
            "ResearchQuery(\"remote work productivity\")\n"
            "  |                                              CCA Domain\n"
            "  v                                              ---------\n"
            "  1. PLAN: Decompose into 4 SubTasks             Agentic Architecture\n"
            "  |    (web, data, docs, facts)\n"
            "  v\n"
            "  2. SORT: Topological sort into 2 waves          Agentic Architecture\n"
            "  |    Wave 0: [web, data, docs] (parallel)\n"
            "  |    Wave 1: [facts] (depends on web, docs)\n"
            "  v\n"
            "  3. DELEGATE: For each task:                     Context Management\n"
            "  |    build_subagent_context() -> explicit string\n"
            "  |    run_agent_loop() with scoped tools          Tool Design\n"
            "  v\n"
            "  4. EVALUATE: fact_checker verifies claims        Reliability\n"
            "  v\n"
            "  5. RESOLVE: conflict_resolver.py                 Reliability\n"
            "  |    reliability ranking -> majority -> human\n"
            "  v\n"
            "  6. SYNTHESIZE: ResearchReport                    All domains\n"
            "       findings + conflicts + gaps + confidence\n"
            "```"
        ),
        _md(
            "## The Three Exam Walkthrough Questions\n\n"
            "The published article walks through three representative CCA exam questions "
            "drawn from the multi-agent research scenario. You have now seen every pattern "
            "they test. Use these as cold-read self-checks.\n\n"
            "Each question below lists the scenario, the correct answer (with a pointer to "
            "the notebook that demonstrates it), and the distractors you'll see on the "
            "actual exam along with *why* each distractor is wrong."
        ),
        _md(
            "### Question 1 -- Context Isolation\n\n"
            "**Scenario.** A coordinator instructs the user to \"use APA citation format.\" "
            "The web-research subagent returns sources formatted in MLA. Why?\n\n"
            "**Correct answer.** The APA instruction lived in the coordinator's message "
            "history but was never placed into the subagent's `task.context`. The "
            "subagent structurally never saw it. The fix is to include formatting "
            "requirements in every `SubTask.context` where they apply.\n\n"
            "**Where to see it.** Notebook 02 (`02_context_isolation.ipynb`) -- the "
            "`run_leaky_subagent` vs `build_subagent_context(task)` cells compare the "
            "two approaches side by side.\n\n"
            "**Distractors and why they fail:**\n\n"
            "- *\"The subagent needs a better system prompt.\"* The system prompt is a "
            "general persona, not a place for query-specific requirements. Putting APA in "
            "every system prompt ever written is not context engineering.\n"
            "- *\"Use a larger model for the subagent.\"* A larger model that still never "
            "sees the instruction will make the same error more fluently.\n"
            "- *\"Let subagents inherit coordinator context automatically.\"* This is the "
            "`shared_context.py` anti-pattern -- it creates token waste, attention "
            "dilution, and privacy-style leakage of other agents' results."
        ),
        _md(
            "### Question 2 -- Tool Overload\n\n"
            "**Scenario.** An agent configured with 18 tools repeatedly selects the wrong "
            "tool for the task. What do you change?\n\n"
            "**Correct answer.** Decompose the single agent into specialized subagents "
            "with 4-5 focused tools each. This is an **architectural** fix -- it is not "
            "a better-descriptions problem.\n\n"
            "**Where to see it.** Notebook 03 (`03_tool_scoping.ipynb`) -- compares "
            "`SUPER_AGENT_TOOLS` (20 on one agent) against `ALL_TOOL_SETS` (5 agents x 4 "
            "each). `tests/test_anti_patterns.py` asserts the super-agent count exceeds "
            "18; `tests/test_tools.py` asserts the focused sets are exactly 4.\n\n"
            "**Distractors and why they fail:**\n\n"
            "- *\"Improve the tool descriptions.\"* Canonical trap. Better descriptions on "
            "18 overlapping tools still cause attention fragmentation; the agent spends "
            "context budget evaluating descriptions rather than executing.\n"
            "- *\"Add a tool-selection preprocessing step.\"* You have added a second "
            "agent to hide the first agent's problem. Now you have two agents to debug "
            "and the underlying attention-fragmentation still exists during selection.\n"
            "- *\"Raise the temperature so the agent is less deterministic.\"* Actively "
            "harmful -- tool selection should be *more* deterministic, not less."
        ),
        _md(
            "### Question 3 -- Silent Failure\n\n"
            "**Scenario.** A research report is missing a critical source after an "
            "upstream API timeout. No error was flagged in the pipeline. What do you "
            "change?\n\n"
            "**Correct answer.** Require **structured error context** from subagents. "
            "Every tool handler returns a `ToolErrorResponse` with `error_type`, "
            "`retry_eligible`, `fallback_available`, and `source`. This gives the "
            "coordinator a decision tree: retry transient failures, fallback for "
            "permanent errors, flag gaps in the final report otherwise.\n\n"
            "**Where to see it.** Notebook 04 (`04_error_handling.ipynb`) -- "
            "`handle_fetch_page_silent` vs the structured `dispatch` on the same timeout "
            "URL, plus the 404 URL which produces a *different* decision tree. Verified "
            "in `tests/test_error_handling.py`.\n\n"
            "**Distractors and why they fail:**\n\n"
            "- *\"Increase timeout duration.\"* Symptom fix. The next slow service still "
            "fails silently; you have just moved the threshold.\n"
            "- *\"Add retry logic.\"* Partially correct -- retry is *one branch* of the "
            "decision tree. It does not help when the failure is a 404 or a permanent "
            "auth error. You cannot build the full decision tree on a response that "
            "refuses to admit failure.\n"
            "- *\"Let the coordinator infer failures from response shape.\"* Requires the "
            "coordinator to know every subagent's internal contract. Brittle. The "
            "`ToolErrorResponse` schema makes the contract explicit and uniform."
        ),
        _md(
            "## CCA Exam Tip\n\n"
            "> The Multi-Agent Research System scenario draws from the three heaviest domains:\n"
            "> - Agentic Architecture (27%)\n"
            "> - Tool Design & MCP (18%)\n"
            "> - Context Management & Reliability (15%)\n"
            ">\n"
            "> Together: **60% of the exam weight**. Master these patterns and you have a "
            "framework for every scenario.\n"
            ">\n"
            "> Key models to know:\n"
            "> - `SubTask` -- the unit of delegation with explicit context\n"
            "> - `ToolErrorResponse` -- structured errors for informed decision-making\n"
            "> - `ConflictRecord` -- deterministic resolution metadata\n"
            "> - `ResearchReport` -- transparent output with gaps and confidence"
        ),
    ])
    _save(nb, "08_integration.ipynb")


def main():
    NOTEBOOKS_DIR.mkdir(exist_ok=True)
    print("Generating notebooks...")
    gen_00()
    gen_01()
    gen_02()
    gen_03()
    gen_04()
    gen_05()
    gen_06()
    gen_07()
    gen_08()
    print(f"\nDone! {9} notebooks generated in {NOTEBOOKS_DIR}")


if __name__ == "__main__":
    main()
