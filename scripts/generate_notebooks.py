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
        _md("# 00 — Setup\n\nVerify your environment is ready for the CCA Multi-Agent Research System notebooks."),
        _code("import sys\nprint(f'Python {sys.version}')"),
        _code("import research_agents\nprint(f'research_agents v{research_agents.__version__}')"),
        _code("from research_agents.services.container import ServiceContainer\nfrom research_agents.data.sources import SEARCH_INDEX\nprint(f'Search index has {len(SEARCH_INDEX)} keyword groups')"),
        _code("# Verify API key (only needed for live demos)\nimport os\nkey = os.environ.get('ANTHROPIC_API_KEY', '')\nif key and key != 'your-api-key-here':\n    print('[OK] ANTHROPIC_API_KEY is set')\nelse:\n    print('[WARN] ANTHROPIC_API_KEY not set — notebooks will use mock mode')", skip=True),
        _md("## Setup Complete\n\nIf all cells above ran without errors, you're ready to proceed to Notebook 01."),
    ])
    _save(nb, "00_setup.ipynb")


# ---- Notebook 01: Hub-and-Spoke Architecture ----

def gen_01():
    nb = _make_nb([
        _md("# 01 — Hub-and-Spoke Architecture\n\n**CCA Pattern**: The coordinator sits at the hub. Specialized subagents are the spokes. Spokes talk only to the hub, never to each other.\n\nThis notebook demonstrates how the coordinator decomposes a research query into subtasks and delegates to specialized agents."),
        _code("import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path('..').resolve()))\nsys.path.insert(0, str(Path('.').resolve()))"),
        _code("from research_agents.models.research import SubTask\nfrom research_agents.agent.coordinator import sort_tasks_into_waves\nfrom research_agents.agent.subagents import SUBAGENT_CONFIGS\nfrom research_agents.tools.definitions import ALL_TOOL_SETS"),
        _md("## Correct Pattern: Specialized Subagents\n\nEach agent has its own system prompt and 4-5 scoped tools."),
        _code("# Show each agent's tool count\nfor agent_type, config in SUBAGENT_CONFIGS.items():\n    print(f'{agent_type}: {len(config.tools)} tools')"),
        _code("# Demonstrate task decomposition into parallel waves\ntasks = [\n    SubTask(task_id='t1', agent_type='web_researcher', instruction='Search for renewable energy data', context='Focus on 2024'),\n    SubTask(task_id='t2', agent_type='data_extractor', instruction='Query capacity statistics', context='renewable_capacity table'),\n    SubTask(task_id='t3', agent_type='fact_checker', instruction='Verify claims', context='', depends_on=['t1', 't2']),\n]\nwaves = sort_tasks_into_waves(tasks)\nfor i, wave in enumerate(waves):\n    task_ids = [t.task_id for t in wave]\n    print(f'Wave {i}: {task_ids} ({\", \".join(t.agent_type for t in wave)})')"),
        _md("## CCA Exam Tip\n\n> When a CCA exam question asks about the correct architecture for a multi-agent system:\n> - **Look for** the option with a single coordinator delegating to specialized subagents\n> - **If an answer** describes subagents communicating directly with each other or sharing context automatically, that is the distractor\n> - The hub-and-spoke pattern keeps coordination centralized"),
    ])
    _save(nb, "01_hub_and_spoke.ipynb")


# ---- Notebook 02: Context Isolation ----

def gen_02():
    nb = _make_nb([
        _md("# 02 — Context Isolation\n\n**CCA Pattern**: Subagents do NOT inherit coordinator context. Each starts blank — it receives ONLY what was explicitly passed.\n\nThis is the concept that trips up more candidates than any other."),
        _code("import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path('..').resolve()))\nsys.path.insert(0, str(Path('.').resolve()))"),
        _code("from research_agents.models.research import SubTask\nfrom research_agents.agent.context_builder import build_subagent_context\nfrom research_agents.agent.agent_loop import AgentResult"),
        _md("## Anti-Pattern: Shared Context\n\nThe coordinator passes its full message history to the subagent."),
        _code("from research_agents.anti_patterns.shared_context import run_leaky_subagent\n\n# Simulate coordinator messages\ncoordinator_messages = [\n    {'role': 'user', 'content': 'Research renewable energy globally'},\n    {'role': 'assistant', 'content': 'I will decompose this into subtasks...'},\n    {'role': 'user', 'content': 'Use APA citation format for all sources'},\n]\n\n# The leaky function converts messages to str() — wasteful and polluting\nleaked_context = str(coordinator_messages)\nprint(f'Leaked context length: {len(leaked_context)} chars')\nprint(f'Contains APA instruction: {\"APA\" in leaked_context}')\nprint(f'Contains coordinator reasoning: {\"decompose\" in leaked_context}')"),
        _md("## Correct Pattern: Explicit Context Passing\n\nThe context builder passes ONLY what the coordinator deliberately selects."),
        _code("# Correct: SubTask contains only explicit context\ntask = SubTask(\n    task_id='t1',\n    agent_type='web_researcher',\n    instruction='Search for renewable energy adoption statistics',\n    context='Focus on 2024 data from government and peer-reviewed sources. Use APA citation format.',\n)\n\nexplicit_context = build_subagent_context(task)\nprint(f'Explicit context length: {len(explicit_context)} chars')\nprint(f'Contains instruction: {\"renewable energy\" in explicit_context}')\nprint(f'Contains APA format: {\"APA\" in explicit_context}')\nprint(f'Contains coordinator reasoning: {\"decompose\" in explicit_context}')\nprint()\nprint(explicit_context)"),
        _code("from helpers import compare_results\n\ncompare_results(\n    {'context_length': len(leaked_context), 'contains_coordinator_reasoning': True, 'contains_other_agent_results': True, 'type': 'str(messages)'},\n    {'context_length': len(explicit_context), 'contains_coordinator_reasoning': False, 'contains_other_agent_results': False, 'type': 'explicit_string'},\n)"),
        _md("## CCA Exam Tip\n\n> Any question where a subagent produces results that 'should have followed the coordinator\\'s instructions' is testing context isolation.\n> - The answer is always that the instructions were in the coordinator's context but never explicitly forwarded\n> - Subagents do not inherit. Subagents receive only what you explicitly send."),
    ])
    _save(nb, "02_context_isolation.ipynb")


# ---- Notebook 03: Tool Scoping ----

def gen_03():
    nb = _make_nb([
        _md("# 03 — Tool Scoping: 4-5 Tools Per Agent\n\n**CCA Pattern**: Each agent gets 4-5 focused tools. The super agent anti-pattern (18+ tools) causes tool selection degradation.\n\nThe exam's official guidance is specific: **keep 4-5 tools per agent**. This is the exam-correct answer."),
        _code("import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path('..').resolve()))\nsys.path.insert(0, str(Path('.').resolve()))"),
        _code("from research_agents.tools.definitions import ALL_TOOL_SETS\nfrom research_agents.anti_patterns.super_agent import SUPER_AGENT_TOOLS, get_super_agent_tool_count"),
        _md("## Anti-Pattern: Super Agent with 18+ Tools"),
        _code("# The super agent has ALL tools combined\nprint(f'Super agent tool count: {get_super_agent_tool_count()}')\nprint()\nprint('All tools on one agent:')\nfor i, tool in enumerate(SUPER_AGENT_TOOLS, 1):\n    print(f'  {i:2d}. {tool[\"name\"]:<25s} {tool[\"description\"][:60]}...')"),
        _md("## Correct Pattern: Focused Tool Sets"),
        _code("# Each agent has 4-5 focused tools\nprint('Focused tool sets:')\nfor agent_type, tools in ALL_TOOL_SETS.items():\n    tool_names = [t['name'] for t in tools]\n    print(f'  {agent_type:<20s} ({len(tools)} tools): {\", \".join(tool_names)}')"),
        _code("from helpers import compare_results\n\ncompare_results(\n    {'total_tools': get_super_agent_tool_count(), 'tools_per_agent': get_super_agent_tool_count(), 'agents': 1},\n    {'total_tools': sum(len(t) for t in ALL_TOOL_SETS.values()), 'tools_per_agent': 4, 'agents': len(ALL_TOOL_SETS)},\n)"),
        _md("## CCA Exam Tip\n\n> The super agent question is one of the most reliable on the CCA exam.\n> Answer choices will include:\n> - 'improve tool descriptions' — WRONG\n> - 'add a tool-selection preprocessing step' — WRONG\n> - **'decompose into specialized subagents with 4-5 tools each' — CORRECT**\n> The improvement is architectural, not descriptive."),
    ])
    _save(nb, "03_tool_scoping.ipynb")


# ---- Notebook 04: Error Handling ----

def gen_04():
    nb = _make_nb([
        _md("# 04 — Structured Error Handling\n\n**CCA Pattern**: Subagents return structured error context so the coordinator can retry, flag gaps, or adjust confidence.\n\n**Anti-pattern**: Silent failures return `{\"status\":\"success\",\"data\":null}` — the coordinator can't tell if the source was empty or failed."),
        _code("import sys, json\nfrom pathlib import Path\nsys.path.insert(0, str(Path('..').resolve()))\nsys.path.insert(0, str(Path('.').resolve()))"),
        _code("from research_agents.tools.handlers import dispatch\nfrom research_agents.anti_patterns.silent_failures import handle_fetch_page_silent\nfrom tests.conftest import make_services\nservices = make_services()"),
        _md("## Anti-Pattern: Silent Failure"),
        _code("# Silent failure on timeout — returns success with null\nsilent_result = json.loads(handle_fetch_page_silent(\n    {'url': 'https://timeout.example.com/remote-data'}, services\n))\nprint('Silent failure response:')\nprint(json.dumps(silent_result, indent=2))\nprint(f'\\nCan coordinator tell this was a timeout? {\"error_type\" in silent_result}')"),
        _md("## Correct Pattern: Structured Error Context"),
        _code("# Structured error on timeout — coordinator gets full decision tree\nstructured_result = json.loads(dispatch(\n    'web_researcher', 'fetch_page',\n    {'url': 'https://timeout.example.com/remote-data'}, services\n))\nprint('Structured error response:')\nprint(json.dumps(structured_result, indent=2))\nprint(f'\\nCan coordinator retry? {structured_result.get(\"retry_eligible\")}')\nprint(f'Error type: {structured_result.get(\"error_type\")}')"),
        _code("from helpers import compare_results\n\ncompare_results(\n    {'status': silent_result['status'], 'has_error_type': 'error_type' in silent_result, 'has_retry_eligible': 'retry_eligible' in silent_result, 'coordinator_can_retry': False},\n    {'status': structured_result['status'], 'has_error_type': 'error_type' in structured_result, 'has_retry_eligible': 'retry_eligible' in structured_result, 'coordinator_can_retry': structured_result.get('retry_eligible', False)},\n)"),
        _md("## CCA Exam Tip\n\n> The silent failure question presents a scenario where a report is missing data.\n> - 'increase timeout duration' — WRONG (addresses symptoms, not root cause)\n> - 'add retry logic' — WRONG (partially helpful but not the core fix)\n> - **'require structured error context from subagents' — CORRECT**"),
    ])
    _save(nb, "04_error_handling.ipynb")


# ---- Notebook 05: Task Decomposition ----

def gen_05():
    nb = _make_nb([
        _md("# 05 — Task Decomposition\n\n**CCA Pattern**: The coordinator decomposes queries into parallel and sequential phases based on data dependencies.\n\nWeb search and document analysis can run in parallel. Fact checking depends on their results, so it runs after."),
        _code("import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path('..').resolve()))\nsys.path.insert(0, str(Path('.').resolve()))"),
        _code("from research_agents.models.research import SubTask\nfrom research_agents.agent.coordinator import sort_tasks_into_waves"),
        _md("## Correct Pattern: Parallel + Sequential Waves"),
        _code("# Define tasks with data dependencies\ntasks = [\n    SubTask(task_id='web', agent_type='web_researcher', instruction='Search for remote work studies', context='Focus on 2024'),\n    SubTask(task_id='data', agent_type='data_extractor', instruction='Query remote work statistics', context='remote_work_stats table'),\n    SubTask(task_id='docs', agent_type='document_analyzer', instruction='Parse Stanford study', context='doc-remote-work-stanford'),\n    SubTask(task_id='facts', agent_type='fact_checker', instruction='Verify claims', context='', depends_on=['web', 'data', 'docs']),\n]\n\nwaves = sort_tasks_into_waves(tasks)\nfor i, wave in enumerate(waves):\n    ids = [t.task_id for t in wave]\n    agents = [t.agent_type for t in wave]\n    print(f'Wave {i}: {ids}')\n    print(f'  Agents: {agents}')\n    print(f'  Can run in parallel: {len(wave) > 1}')\n    print()"),
        _code("# Compare: all sequential (no parallelism)\nsequential_tasks = [\n    SubTask(task_id='web', agent_type='web_researcher', instruction='a', context=''),\n    SubTask(task_id='data', agent_type='data_extractor', instruction='b', context='', depends_on=['web']),\n    SubTask(task_id='docs', agent_type='document_analyzer', instruction='c', context='', depends_on=['data']),\n    SubTask(task_id='facts', agent_type='fact_checker', instruction='d', context='', depends_on=['docs']),\n]\nseq_waves = sort_tasks_into_waves(sequential_tasks)\nprint(f'Parallel waves: {len(waves)} (wave 0 has {len(waves[0])} tasks)')\nprint(f'Sequential waves: {len(seq_waves)} (all single-task waves)')"),
        _md("## CCA Exam Tip\n\n> Task decomposition questions ask whether two subtasks should run in parallel or sequentially.\n> - If Subtask B needs output from Subtask A → sequential\n> - If they work from independent inputs → parallel\n> - 'Web search' and 'document parsing' are the canonical parallel pair\n> - 'Fact checking' and 'report writing' are always sequential"),
    ])
    _save(nb, "05_task_decomposition.ipynb")


# ---- Notebook 06: Conflict Resolution ----

def gen_06():
    nb = _make_nb([
        _md("# 06 — Conflict Resolution\n\n**CCA Pattern**: The coordinator resolves contradictions using deterministic strategies:\n1. Source reliability ranking\n2. Majority consensus\n3. Flag for human review\n\nThis is programmatic enforcement — not LLM judgment."),
        _code("import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path('..').resolve()))\nsys.path.insert(0, str(Path('.').resolve()))"),
        _code("from research_agents.agent.conflict_resolver import resolve_conflict, resolve_conflicts\nfrom research_agents.models.research import SourceReliability"),
        _md("## Correct Pattern: Deterministic Resolution"),
        _code("# Strategy 1: High-reliability source beats low-reliability\nreliability = {\n    'https://energy.gov/renewable-2024': SourceReliability.HIGH,\n    'https://energyblog.example.com/renewables': SourceReliability.LOW,\n}\nrecord = resolve_conflict(\n    claim='Renewable energy accounts for 30% of global electricity',\n    sources_for=['https://energy.gov/renewable-2024'],\n    sources_against=['https://energyblog.example.com/renewables'],\n    reliability_lookup=reliability,\n)\nprint(f'Claim: {record.claim}')\nprint(f'Resolution: {record.resolution}')\nprint(f'Confidence: {record.confidence:.2f}')"),
        _code("# Strategy 3: Equal reliability + equal count → human review\nreliability_equal = {\n    'https://reuters.com': SourceReliability.MEDIUM,\n    'https://bbc.com': SourceReliability.MEDIUM,\n}\nrecord2 = resolve_conflict(\n    claim='Remote work productivity',\n    sources_for=['https://reuters.com'],\n    sources_against=['https://bbc.com'],\n    reliability_lookup=reliability_equal,\n)\nprint(f'Resolution: {record2.resolution}')\nprint(f'Confidence: {record2.confidence:.2f}')"),
        _md("## CCA Exam Tip\n\n> The conflict resolution question tests whether you understand that:\n> - Source reliability ranking is the first strategy\n> - Majority consensus applies when reliability is tied\n> - Human review is the fallback, not auto-resolution\n> - 'First result wins' is always the wrong answer"),
    ])
    _save(nb, "06_conflict_resolution.ipynb")


# ---- Notebook 07: MCP Primitives ----

def gen_07():
    nb = _make_nb([
        _md("# 07 — MCP Primitives\n\n**CCA Pattern**: MCP defines three primitives:\n- **Tools** — executable functions an agent can invoke (verbs)\n- **Resources** — data schemas and catalogs agents can query (nouns)\n- **Prompts** — templates for common operations (patterns)\n\nThe exam tests whether you know the difference."),
        _code("import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path('..').resolve()))\nsys.path.insert(0, str(Path('.').resolve()))"),
        _code("from research_agents.tools.definitions import ALL_TOOL_SETS"),
        _md("## Tools (Verbs) — Things the Agent Does"),
        _code("# Our tool definitions are MCP Tools — executable functions\nfor agent_type, tools in ALL_TOOL_SETS.items():\n    print(f'{agent_type}:')\n    for tool in tools:\n        print(f'  Tool: {tool[\"name\"]:<25s} (action/verb)')"),
        _md("## Resources (Nouns) — Things the Agent Reads\n\nIn our system, these would be:\n- The document catalog (list of available documents)\n- The source reliability database\n- The database table schemas\n\nResources are NOT tools — they are data the agent can query."),
        _code("# Resources in our system (conceptual mapping)\nresources = {\n    'document_catalog': 'List of available research documents and their metadata',\n    'source_reliability_db': 'Database of source URLs and their reliability ratings',\n    'database_schemas': 'Schemas for available statistical tables',\n}\nfor name, desc in resources.items():\n    print(f'  Resource: {name:<25s} (data/noun)')"),
        _md("## Prompts (Patterns) — Templates the Agent Uses\n\nIn our system:\n- Research query decomposition template\n- Citation format template (APA, MLA)\n- Error report template"),
        _code("# Prompts in our system (conceptual mapping)\nprompts = {\n    'research_query_template': 'Template for decomposing a query into subtasks',\n    'citation_format_template': 'Template for formatting citations (APA)',\n    'error_report_template': 'Template for reporting structured errors',\n}\nfor name, desc in prompts.items():\n    print(f'  Prompt: {name:<30s} (template/pattern)')"),
        _md("## CCA Exam Tip\n\n> The MCP primitives question is a vocabulary test:\n> - **Tools** are things the agent *does* (verbs)\n> - **Resources** are things the agent *reads* (nouns)\n> - **Prompts** are templates the agent *uses* (patterns)\n>\n> If a question describes a source reliability database → **Resource**, not a Tool.\n> If it describes a function that verifies a claim → **Tool**."),
    ])
    _save(nb, "07_mcp_primitives.ipynb")


# ---- Notebook 08: Integration ----

def gen_08():
    nb = _make_nb([
        _md("# 08 — Integration: Full End-to-End Research Query\n\nThis notebook brings together all CCA patterns:\n- Hub-and-spoke coordinator\n- Context isolation via explicit passing\n- 4-5 scoped tools per agent\n- Structured error handling\n- Parallel + sequential task waves\n- Deterministic conflict resolution"),
        _code("import sys, json\nfrom pathlib import Path\nsys.path.insert(0, str(Path('..').resolve()))\nsys.path.insert(0, str(Path('.').resolve()))"),
        _code("from research_agents.models.research import SubTask\nfrom research_agents.agent.coordinator import sort_tasks_into_waves, run_coordinator, build_research_report\nfrom research_agents.agent.context_builder import build_subagent_context\nfrom research_agents.agent.subagents import SUBAGENT_CONFIGS\nfrom research_agents.data.scenarios import SCENARIOS\nfrom research_agents.data.sources import SOURCE_RELIABILITY_RATINGS\nfrom research_agents.models.research import SourceReliability\nfrom tests.conftest import make_services"),
        _md("## Scenario: Remote Work Economic Impact\n\nThis scenario tests both conflict resolution AND error handling."),
        _code("scenario = SCENARIOS['economic_impact']\nprint(f'Query: {scenario.query}')\nprint(f'Expected agents: {scenario.expected_agents}')\nprint(f'Expected conflicts: {scenario.expected_conflicts}')\nprint(f'Expected gaps: {scenario.expected_gaps}')"),
        _md("## Step 1: Task Decomposition"),
        _code("# Decompose into subtasks (normally the LLM does this)\ntasks = [\n    SubTask(task_id='web', agent_type='web_researcher',\n        instruction='Search for studies on remote work and productivity',\n        context='Focus on 2024 data. Look for both pro and con evidence.'),\n    SubTask(task_id='data', agent_type='data_extractor',\n        instruction='Query remote work statistics from the database',\n        context='Use the remote_work_stats table'),\n    SubTask(task_id='docs', agent_type='document_analyzer',\n        instruction='Analyze the Stanford remote work study',\n        context='Document ID: doc-remote-work-stanford'),\n    SubTask(task_id='facts', agent_type='fact_checker',\n        instruction='Verify productivity claims from web and document sources',\n        context='Check claims about remote work productivity impact',\n        depends_on=['web', 'docs']),\n]\n\nwaves = sort_tasks_into_waves(tasks)\nfor i, wave in enumerate(waves):\n    print(f'Wave {i}: {[t.task_id for t in wave]} ({\"parallel\" if len(wave) > 1 else \"sequential\"})' )"),
        _md("## Step 2: Context Isolation Check\n\nEach subagent gets ONLY its explicit context."),
        _code("for task in tasks:\n    ctx = build_subagent_context(task)\n    print(f'{task.task_id} ({task.agent_type}):')\n    print(f'  Context length: {len(ctx)} chars')\n    print(f'  First 100 chars: {ctx[:100]}...')\n    print()"),
        _md("## Step 3: Run Coordinator (Mock Mode)\n\nUsing mock client for reproducible results."),
        _code("from types import SimpleNamespace\n\ncall_count = 0\ndef mock_create(**kwargs):\n    global call_count\n    call_count += 1\n    agent_responses = {\n        1: 'Found 4 sources. McKinsey reports +13% productivity. Blog claims -20%.',\n        2: 'Remote work stats: 9.4% fully remote, 18.2% hybrid in 2024.',\n        3: 'Stanford study: hybrid workers 13% more productive, 24% higher satisfaction.',\n        4: 'Verified: +13% claim supported by multiple sources. -20% claim unsupported.',\n    }\n    text = agent_responses.get(call_count, 'Analysis complete.')\n    return SimpleNamespace(\n        content=[SimpleNamespace(type='text', text=text)],\n        stop_reason='end_turn',\n        usage=SimpleNamespace(input_tokens=500, output_tokens=200),\n    )\n\nmock_client = SimpleNamespace(messages=SimpleNamespace(create=mock_create))\nservices = make_services()\n\nresults, waves = run_coordinator(mock_client, services, tasks)\nfor task_id, result in results.items():\n    print(f'{task_id}: {result.content[:80]}...' if len(result.content) > 80 else f'{task_id}: {result.content}')"),
        _md("## Step 4: Conflict Resolution + Report"),
        _code("# Build report with conflict resolution\nconflicts = [{\n    'claim': 'Remote workers are more productive',\n    'sources_for': ['https://mckinsey.com/future-of-work', 'https://bls.gov/remote-work-stats'],\n    'sources_against': ['https://workfromhome-blog.example.com/productivity'],\n}]\n\nreliability = {url: rel for url, rel in SOURCE_RELIABILITY_RATINGS.items()}\n\nreport = build_research_report(\n    query=scenario.query,\n    results=results,\n    reliability_lookup=reliability,\n    conflicts=conflicts,\n    gaps=['https://timeout.example.com/remote-data (timeout)'],\n)\n\nprint(f'Query: {report.query}')\nprint(f'Findings: {len(report.findings)}')\nprint(f'Conflicts resolved: {len(report.conflicts)}')\nfor c in report.conflicts:\n    print(f'  - {c.claim}: {c.resolution} (confidence: {c.confidence:.2f})')\nprint(f'Gaps: {report.gaps}')\nprint(f'Confidence score: {report.confidence_score:.2f}')"),
        _md("## CCA Exam Tip\n\n> The Multi-Agent Research System scenario draws from the three heaviest domains:\n> - Agentic Architecture (27%)\n> - Tool Design & MCP (18%)\n> - Context Management & Reliability (15%)\n>\n> Together: **60% of the exam weight**. Master these patterns and you have a framework for every scenario."),
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
