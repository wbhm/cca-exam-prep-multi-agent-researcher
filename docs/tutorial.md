# CCA Multi-Agent Research System: A Deep Tutorial

This tutorial walks through every module in the Multi-Agent Research System project, explaining the architecture, the code, and -- critically -- the **CCA exam patterns** each piece demonstrates. By the end, you will understand how to build a production-quality multi-agent system that enforces context isolation, scopes tools correctly, handles errors transparently, and resolves conflicts deterministically.

The project has two layers:

1. **The Python package** (`src/research_agents/`) -- production-quality implementation with only correct patterns.
2. **The anti-patterns** (`src/research_agents/anti_patterns/`) -- deliberately wrong implementations that demonstrate what happens when you ignore CCA guidance.

We will cover both, because understanding *why* the wrong way fails is how you internalize the right way before exam day.

---

## Table of Contents

1. [Project Architecture Overview](#1-project-architecture-overview)
2. [Data Models -- The Foundation](#2-data-models----the-foundation)
3. [Services -- Simulated Business Systems](#3-services----simulated-business-systems)
4. [Seed Data -- Sources, Documents, and Scenarios](#4-seed-data----sources-documents-and-scenarios)
5. [Tool Definitions -- Telling Claude What It Can Do](#5-tool-definitions----telling-claude-what-it-can-do)
6. [Tool Handlers -- Executing Tool Calls](#6-tool-handlers----executing-tool-calls)
7. [The Agent Loop -- Stop-Reason-Driven Execution](#7-the-agent-loop----stop-reason-driven-execution)
8. [Context Isolation -- The Enforcer](#8-context-isolation----the-enforcer)
9. [Subagent Configuration -- System Prompts and Tool Sets](#9-subagent-configuration----system-prompts-and-tool-sets)
10. [The Coordinator -- Hub-and-Spoke Orchestration](#10-the-coordinator----hub-and-spoke-orchestration)
11. [Conflict Resolution -- Deterministic Strategies](#11-conflict-resolution----deterministic-strategies)
12. [Anti-Pattern 1: Super Agent (18+ Tools)](#12-anti-pattern-1-super-agent-18-tools)
13. [Anti-Pattern 2: Shared Context (Leaky Coordinator)](#13-anti-pattern-2-shared-context-leaky-coordinator)
14. [Anti-Pattern 3: Silent Failures](#14-anti-pattern-3-silent-failures)
15. [MCP Primitives -- Tools, Resources, and Prompts](#15-mcp-primitives----tools-resources-and-prompts)
16. [How the Pieces Connect -- End-to-End Data Flow](#16-how-the-pieces-connect----end-to-end-data-flow)

---

## 1. Project Architecture Overview

```
src/research_agents/
  models/          Pydantic data models (SubTask, ResearchReport, errors)
  services/        4 simulated research services + ServiceContainer
  data/            Pre-built data with contradictions + error triggers
  tools/           Claude API tool schemas + per-agent-type handlers
  agent/           Coordinator, agent loop, context builder, conflict resolver
  anti_patterns/   3 deliberately wrong implementations, each runnable through the loop
  testing.py       Scripted client: replay a fixed transcript through the real loop
```

The data flows like this:

```
Research query
  -> the caller decomposes it into SubTasks with depends_on fields
  -> sort_tasks_into_waves() topologically sorts into parallel waves
  -> for each wave: context_builder.py builds EXPLICIT context string
  -> run_agent_loop() calls the client with SCOPED tools per agent type
     and logs every tool call and its JSON result
  -> handlers.py dispatches tool calls via DISPATCH[agent_type][tool_name]
  -> conflict_resolver.py resolves contradictions DETERMINISTICALLY
  -> collect_gaps() turns structured tool errors into report gaps
  -> build_research_report() compiles findings, conflicts, gaps
```

No notebook or test calls the Claude API. `research_agents/testing.py` provides `scripted_client()`, which replays a list of pre-written model responses (`text_turn`, `tool_turn`) through the real loop, so the dispatch, tool results, message history and stop reasons are all genuine while the model's turns are fixed. Replaying one transcript through two routers is how every anti-pattern in this project is demonstrated.

Every layer enforces a CCA principle:

| Layer | CCA Principle |
|-------|--------------|
| Models | Type safety via Pydantic -- invalid data is rejected at construction |
| Services | Simulated business logic -- deterministic, in-memory |
| Tools | Exactly 4 focused tools per agent with negative-bound descriptions |
| Context Builder | Structural isolation -- coordinator messages are never a function parameter |
| Agent Loop | Stop-reason-driven loop (control flow branches on `stop_reason`, not on block types) |
| Coordinator | Hub-and-spoke -- subagents talk only to coordinator, never to each other |
| Conflict Resolver | Programmatic enforcement -- deterministic rules, not LLM judgment |

---

## 2. Data Models -- The Foundation

**File:** `src/research_agents/models/research.py`

Every data structure in the system is a Pydantic `BaseModel`. Pydantic provides runtime type validation, so invalid data fails at construction time rather than silently corrupting downstream logic.

### SourceReliability

```python
class SourceReliability(StrEnum):
    HIGH = "high"      # peer-reviewed, .gov, official statistics
    MEDIUM = "medium"  # established news outlets, .edu
    LOW = "low"        # blogs, unverified sources
    UNKNOWN = "unknown"  # reliability not yet assessed
```

`StrEnum` (Python 3.11+) means each variant is both an enum member *and* a string. You can pass `SourceReliability.HIGH` anywhere a string is expected, and it serializes cleanly to JSON. This enum drives the conflict resolution scoring system: HIGH = 3 points, MEDIUM = 2, LOW = 1, UNKNOWN = 0.

### ResearchQuery

```python
class ResearchQuery(BaseModel):
    query: str
    depth: str = "standard"    # "quick", "standard", "deep"
    required_sources: int = 3
```

The input to the coordinator. The `depth` field would control how many subagent waves are spawned, and `required_sources` sets the minimum number of sources the report needs before it can be considered complete.

### SubTask -- The Unit of Delegation

```python
class SubTask(BaseModel):
    task_id: str            # Unique identifier for dependency tracking
    agent_type: str         # "web_researcher", "document_analyzer", etc.
    instruction: str        # What to do
    context: str            # Explicitly passed context (NOT inherited)
    depends_on: list[str] = Field(default_factory=list)  # task_ids for sequential ordering
```

This is the most important model in the system. Each field maps directly to a CCA concept:

- **`task_id`**: Used by `sort_tasks_into_waves()` for topological sorting and by `build_subagent_context()` for predecessor result filtering.
- **`agent_type`**: Maps to a `SubagentConfig` in the registry, which provides the system prompt and scoped tools.
- **`instruction`**: What the subagent should do. This is always present in the context string.
- **`context`**: Contains **only** what the coordinator explicitly chose to pass. This is not the coordinator's conversation history. This is not other subagents' results. This is a deliberately selected string.
- **`depends_on`**: The only mechanism that creates sequential ordering. Tasks with empty `depends_on` are independent and can run in parallel.

The `context` field is the heart of context isolation. The coordinator must explicitly decide what information to include. If the coordinator has citation format rules in its system prompt but doesn't include them in `context`, the subagent has no knowledge of them. This is by design.

### SearchResult and PageContent

```python
class SearchResult(BaseModel):
    url: str
    title: str
    snippet: str
    reliability: SourceReliability = SourceReliability.UNKNOWN

class PageContent(BaseModel):
    url: str
    title: str
    text: str
    reliability: SourceReliability = SourceReliability.UNKNOWN
```

These are the output types from the web search service. `SearchResult` is what comes back from a search query (metadata only). `PageContent` is the full page text retrieved by URL. Both carry a `reliability` rating that feeds into conflict resolution.

### Document and DocumentSection

```python
class Document(BaseModel):
    doc_id: str
    title: str
    sections: list[DocumentSection] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    reliability: SourceReliability = SourceReliability.MEDIUM

class DocumentSection(BaseModel):
    heading: str
    content: str
    claims: list[str] = Field(default_factory=list)  # Extractable factual claims
```

Documents are research papers with internal structure. The `claims` field on each section is key -- these are the factual statements that the fact checker agent verifies. Some claims in the test data deliberately contradict each other to trigger conflict resolution.

### FactRecord

```python
class FactRecord(BaseModel):
    claim: str
    verified: bool
    confidence: float = Field(ge=0.0, le=1.0)
    source: str
    reliability: SourceReliability = SourceReliability.HIGH
```

A verified (or debunked) fact from the knowledge base. The `verified` field is a boolean -- the knowledge base knows whether the claim is true or false. The `confidence` field indicates how certain the knowledge base is. Notice that `verified=False` with `confidence=0.10` means "we are quite sure this is wrong."

### SourceResult

```python
class SourceResult(BaseModel):
    source_url: str
    title: str
    content_summary: str
    reliability: SourceReliability
    claims: list[str] = Field(default_factory=list)
```

The aggregated output from a single source, used in the final report. In this package `build_research_report()` produces one per subagent transcript (`source_url="agent:<task_id>"`, reliability stamped `HIGH`), not one per underlying web source; the per-source ratings live in the conflict records.

### ConflictRecord

```python
class ConflictRecord(BaseModel):
    claim: str
    sources_for: list[str]       # Source URLs that support the claim
    sources_against: list[str]   # Source URLs that contradict the claim
    resolution: str              # "majority", "highest_reliability", "flagged_for_human"
    confidence: float = Field(ge=0.0, le=1.0)
    winning_side: str = "undecided"  # "for", "against", or "undecided"
```

A documented contradiction between sources, with resolution metadata. The `resolution` field records *which strategy* was used (reliability ranking, majority vote, or human flag). `winning_side` records *which way* it went; without it a consumer could not tell whether the claim was upheld. The `confidence` field reflects how certain the resolution is. This is one of the key CCA concepts: the coordinator must resolve contradictions using **deterministic strategies**, not LLM judgment.

### ResearchReport

```python
class ResearchReport(BaseModel):
    query: str
    findings: list[SourceResult] = Field(default_factory=list)
    conflicts: list[ConflictRecord] = Field(default_factory=list)
    synthesis: str = ""
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    gaps: list[str] = Field(default_factory=list)  # sources that failed/were unavailable
```

The final output of the coordinator. The `gaps` field is critical -- it records sources that were unavailable (timeouts, errors) so the report is transparent about its limitations. `build_research_report()` derives it from the subagents' structured tool errors (Section 10), never from the model's prose. A report that says "we could not reach Source X" is more trustworthy than one that silently omits it.

---

## 3. Services -- Simulated Business Systems

**Directory:** `src/research_agents/services/`

The project simulates four research services that a real multi-agent system would integrate with. All are in-memory -- students need zero infrastructure setup.

### WebSearchService

```python
class WebSearchService:
    def __init__(self, search_index, pages, timeout_urls=None, not_found_urls=None):
        self._search_index = search_index     # keyword -> list[SearchResult]
        self._pages = pages                   # URL -> PageContent
        self._timeout_urls = timeout_urls      # URLs that simulate timeouts
        self._not_found_urls = not_found_urls  # URLs that simulate 404s

    def search(self, query: str) -> list[SearchResult]:
        # Keyword matching against the search index
        ...

    def fetch_page(self, url: str) -> PageContent:
        # May raise WebSearchTimeoutError or WebSearchNotFoundError
        ...
```

Two custom exceptions here: `WebSearchTimeoutError` and `WebSearchNotFoundError`. These are caught by tool handlers and converted to structured error responses. The `timeout_urls` and `not_found_urls` sets allow the test data to trigger specific error paths deterministically.

The search implementation uses simple keyword matching: for each keyword in the search index, if that keyword appears in the query string (case-insensitive), the corresponding results are included. This is sufficient for demonstrating the architectural patterns without needing a real search engine.

### DocumentStore

```python
class DocumentStore:
    def __init__(self, documents: dict[str, Document]):
        self._documents = documents

    def get_document(self, doc_id: str) -> Document:
        if doc_id not in self._documents:
            raise DocumentNotFoundError(f"Document not found: {doc_id}")
        return self._documents[doc_id]

    def list_documents(self) -> list[Document]:
        ...

    def search_by_title(self, keyword: str) -> list[Document]:
        ...
```

Simple dictionary lookup by `doc_id`. The `DocumentNotFoundError` is caught by the document analyzer tool handler and returned as a structured error. Note there are no defensive copies here (unlike the customer service project's `CustomerDatabase`) because documents are not mutated during processing.

### DatabaseService

```python
class DatabaseService:
    def __init__(self, tables: dict[str, list[dict]]):
        self._tables = tables

    def query(self, table: str, filters: dict | None = None) -> list[dict]:
        if table not in self._tables:
            raise TableNotFoundError(f"Table not found: {table}")
        rows = self._tables[table]
        if not filters:
            return rows
        return [row for row in rows
                if all(row.get(k) == v for k, v in filters.items())]

    def get_schema(self, table: str) -> dict:
        # Infers column names and types from the first row
        ...
```

Named tables of dictionaries with optional exact-match filtering. The schema inference examines the first row's keys and value types. This service backs the data extractor agent's tools.

### KnowledgeBase

```python
class KnowledgeBase:
    def __init__(self, facts: list[FactRecord], source_reliability: dict[str, SourceReliability]):
        self._facts = facts
        self._source_reliability = source_reliability

    def lookup_fact(self, claim: str) -> list[FactRecord]:
        # Facts scored by shared words, closest match first
        ...

    def get_source_reliability(self, url: str) -> SourceReliability:
        return match_reliability(url, self._source_reliability)
```

The knowledge base serves two purposes: fact verification and source reliability scoring. `lookup_fact` scores every stored fact by how many of its words (three or more characters) appear in the claim and returns matches by descending overlap. The ranking matters: the verified "30% renewable" record and the debunked "45% renewable" record share most of their words, and a fact checker that simply took the highest-confidence match would certify the debunked claim as true. `handle_verify_claim` takes the first match.

`get_source_reliability` delegates to `services/reliability.match_reliability()`: exact URL match first, then domain match (`"energy.gov"` matches `"https://energy.gov/renewable-2024"`), then `UNKNOWN`. The conflict resolver uses the same function, so the domain-keyed `SOURCE_RELIABILITY_RATINGS` can be passed straight into `resolve_conflict()`.

### ServiceContainer -- Dependency Injection

```python
@dataclass(frozen=True)
class ServiceContainer:
    web_search: WebSearchService
    document_store: DocumentStore
    database: DatabaseService
    knowledge_base: KnowledgeBase
```

A frozen dataclass holding all four services. `frozen=True` means you cannot reassign fields after construction -- the container is immutable. Every tool handler receives this single object and accesses exactly the services it needs. Services are never imported directly in tool modules.

This is dependency injection. If you want to swap `WebSearchService` for a real API client in production, you construct a different `ServiceContainer`. The tool handlers don't change.

`make_default_services()` in the same module builds a fresh container over the seed data in `data/sources.py`. The notebooks and the test fixture both use it.

---

## 4. Seed Data -- Sources, Documents, and Scenarios

**Directory:** `src/research_agents/data/`

### sources.py -- Pre-Built Data with Contradictions

This file contains all the in-memory data for the four services. The data is carefully crafted to trigger specific architectural patterns:

#### Search Index

Three keyword groups with deliberate contradictions:

| Keyword | Sources | Contradiction |
|---------|---------|--------------|
| `renewable energy` | energy.gov (HIGH), Reuters (MEDIUM), energyblog (LOW) | Blog claims 45% vs .gov claims 30% |
| `ai healthcare` | nih.gov (HIGH), Nature (HIGH), healthtech blog (LOW) | Blog URL returns 404 |
| `remote work economic` | bls.gov (HIGH), McKinsey (MEDIUM), blog (LOW), timeout URL | Blog claims -20% vs McKinsey +13%; one URL times out |

#### Intentional Failures

```python
TIMEOUT_URLS = {"https://timeout.example.com/remote-data"}
NOT_FOUND_URLS = {"https://healthtech.example.com/ai-revolution"}
```

These URLs trigger `WebSearchTimeoutError` and `WebSearchNotFoundError` respectively. They exist to demonstrate the difference between structured error handling and silent failures.

#### Documents

Three research documents with sections containing extractable claims:

- `doc-renewable-iea`: IEA World Energy Outlook with capacity growth claims
- `doc-ai-health-review`: Systematic review with AI diagnostic accuracy claims
- `doc-remote-work-stanford`: Stanford study with productivity claims

#### Database Tables

Three structured data tables:

- `renewable_capacity`: Solar and wind capacity by year (2020-2024)
- `remote_work_stats`: Remote/hybrid/office percentages by year
- `ai_healthcare_metrics`: AI vs human accuracy by medical modality

#### Knowledge Base

Five verified facts that directly correspond to claims in the web search results and documents. Notably:

- "Renewable energy accounts for 30% of global electricity" -- `verified=True`, `confidence=0.95`
- "Renewable energy accounts for 45% of global electricity" -- `verified=False`, `confidence=0.10`
- "Remote workers are 13% more productive" -- `verified=True`, `confidence=0.80`
- "Remote workers are 20% less productive" -- `verified=False`, `confidence=0.05`

This data structure means the fact checker can definitively verify or debunk claims, which feeds into the conflict resolver.

#### Source Reliability Ratings

```python
SOURCE_RELIABILITY_RATINGS = {
    "energy.gov": SourceReliability.HIGH,
    "nih.gov": SourceReliability.HIGH,
    "bls.gov": SourceReliability.HIGH,
    "nature.com": SourceReliability.HIGH,
    "reuters.com": SourceReliability.MEDIUM,
    "mckinsey.com": SourceReliability.MEDIUM,
    "energyblog.example.com": SourceReliability.LOW,
    "healthtech.example.com": SourceReliability.LOW,
    "workfromhome-blog.example.com": SourceReliability.LOW,
    "timeout.example.com": SourceReliability.MEDIUM,
}
```

These ratings drive the conflict resolver's first strategy: reliability ranking. They are keyed by domain while conflicts carry full URLs; `match_reliability()` bridges the two.

One quirk of `WebSearchService.search` worth knowing: an index key matches only when it appears verbatim in the query. `"remote work economic"` is a key, so a scripted `search_web` call must contain that phrase; the scenario's own query string ("...economic impact of remote work...") would return nothing.

### scenarios.py -- Pre-Defined Research Scenarios

```python
@dataclass(frozen=True)
class ResearchScenario:
    name: str
    query: str
    expected_agents: list[str]
    expected_conflicts: int
    expected_gaps: int
    description: str
```

Three scenarios, each designed to trigger specific CCA patterns:

| Scenario | Tests | Conflicts | Gaps | Key Pattern |
|----------|-------|-----------|------|-------------|
| `climate_renewable` | Conflict resolution | 1 (blog vs .gov) | 0 | Reliability ranking resolves conflict |
| `ai_healthcare` | Error handling | 0 | 1 (404) | Structured error reports missing source |
| `economic_impact` | Both | 1 (+13% vs -20%) | 1 (timeout) | Conflict resolution + error handling combined |

Each scenario documents its expected tool chain and outcome. This makes scenarios both teaching artifacts (students can trace the expected flow) and test oracles (automated tests can verify the actual flow matches).

---

## 5. Tool Definitions -- Telling Claude What It Can Do

**File:** `src/research_agents/tools/definitions.py`

This file defines the tool sets for all 5 agent types. The CCA exam tests whether you know the right number (4-5 per agent) and whether your descriptions include negative bounds.

### The 4-Tool-Per-Agent Structure

Each agent type has exactly 4 tools:

| Agent Type | Tools |
|-----------|-------|
| Web Researcher | `search_web`, `fetch_page`, `extract_text`, `summarize_source` |
| Document Analyzer | `parse_document`, `extract_sections`, `identify_claims`, `check_citations` |
| Data Extractor | `query_database`, `transform_data`, `validate_schema`, `format_output` |
| Fact Checker | `verify_claim`, `cross_reference`, `score_reliability`, `flag_conflict` |
| Coordinator | `delegate_task`, `collect_results`, `resolve_conflicts`, `compile_report` |

### Tool Schema Format

Each tool follows the Claude API format:

```python
{
    "name": "search_web",
    "description": (
        "Search the public web for information matching a query. "
        "Returns URLs, titles, and snippets. "
        "Does NOT fetch full page content (use fetch_page for that). "
        "Does NOT search internal documents or databases."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query string"},
        },
        "required": ["query"],
    },
}
```

### Negative-Bound Descriptions

Every tool description says what the tool does *and what it does not do*. This is the CCA negative-bound pattern. Without "Does NOT fetch full page content," Claude might try to use `search_web` to get page text. Without "Does NOT search internal documents," Claude might call it when it needs `parse_document`.

The `Does NOT` phrases prevent misrouting. This is the exam-correct approach -- validation inside the tool doesn't fix the routing problem, because by the time the tool runs, Claude has already made the wrong choice.

### The Coordinator's Tools

The coordinator's tools are particularly interesting:

```python
{
    "name": "delegate_task",
    "description": (
        "Delegate a subtask to a specialized subagent. "
        "Specify the agent type, instruction, and explicit context. "
        "The subagent receives ONLY what you pass here -- it has no "
        "access to your conversation history or other subagent results. "
        "Does NOT execute the task itself (subagents do the work)."
    ),
    ...
}
```

This tool description explicitly tells the coordinator that "The subagent receives ONLY what you pass here." This is context isolation enforced at the prompt level in addition to the structural enforcement in `build_subagent_context()`.

### ALL_TOOL_SETS Convenience Dict

```python
ALL_TOOL_SETS: dict[str, list[dict]] = {
    "web_researcher": WEB_RESEARCHER_TOOLS,
    "document_analyzer": DOCUMENT_ANALYZER_TOOLS,
    "data_extractor": DATA_EXTRACTOR_TOOLS,
    "fact_checker": FACT_CHECKER_TOOLS,
    "coordinator": COORDINATOR_TOOLS,
}
```

Used by notebooks for iteration and display. Never used at runtime -- the actual tool routing goes through `SubagentConfig` objects.

---

## 6. Tool Handlers -- Executing Tool Calls

**Directory:** `src/research_agents/tools/`

Each agent type has its own handler module. All handlers follow the same signature:

```python
def handle_<tool_name>(input_dict: dict, services: ServiceContainer) -> str:
```

Input is a dict (from Claude's `tool_use` block's `input` field). Output is **always** a JSON string -- matching the Claude API's `tool_result` content format.

### The Dispatch Registry

**File:** `src/research_agents/tools/handlers.py`

```python
DISPATCH: dict[str, dict[str, Handler]] = {
    "web_researcher": {
        "search_web": handle_search_web,
        "fetch_page": handle_fetch_page,
        "extract_text": handle_extract_text,
        "summarize_source": handle_summarize_source,
    },
    "document_analyzer": { ... },
    "data_extractor": { ... },
    "fact_checker": { ... },
    "coordinator": { ... },
}
```

The dispatch is a nested dict: agent type first, then tool name. A tool is reachable only through the agent that owns it, so a web researcher asking for `query_database` gets a structured `invalid_input` error rather than the database. Even if two different agent types had a tool called `search`, they would route to different handler functions.

The `dispatch()` function handles routing:

```python
def dispatch(agent_type: str, tool_name: str, input_dict: dict, services: ServiceContainer) -> str:
    agent_handlers = DISPATCH.get(agent_type)
    if agent_handlers is None:
        return error_response("invalid_input", "dispatch", f"Unknown agent_type: {agent_type}")
    handler = agent_handlers.get(tool_name)
    if handler is None:
        return error_response(
            "invalid_input", "dispatch", f"Unknown tool '{tool_name}' for agent '{agent_type}'"
        )
    return handler(input_dict, services)
```

Note: on dispatch errors (unknown agent type or tool name), it returns a structured error JSON string. It never raises exceptions. This is the CCA pattern: tool handlers always return JSON strings, never exceptions.

`dispatch` has the signature `(agent_type, tool_name, input_dict, services) -> str`, and `run_agent_loop()` accepts any function with that signature as `dispatch_fn`. That is how the anti-pattern routers (`super_agent_dispatch`, `silent_dispatch`) are injected in the notebooks.

### error_response() -- One Constructor for Every Error

**File:** `src/research_agents/tools/_errors.py`

```python
def error_response(
    error_type: str,
    source: str,
    message: str,
    *,
    retry_eligible: bool = False,
    fallback_available: bool = False,
    partial_data: dict | None = None,
) -> str:
    return ToolErrorResponse(...).model_dump_json()
```

Every handler builds its failure payload through this function, so the JSON on the wire is a serialized `ToolErrorResponse` by construction. `tests/test_error_handling.py` parses every error path back through `ToolErrorResponse.model_validate` to prove it.

### Example Handler: handle_fetch_page

```python
def handle_fetch_page(input_dict: dict, services: ServiceContainer) -> str:
    url = input_dict.get("url", "")
    if not url:
        return error_response("invalid_input", "fetch_page", "URL parameter is required")
    try:
        page = services.web_search.fetch_page(url)
        return json.dumps({"status": "success", "data": page.model_dump()})
    except WebSearchTimeoutError:
        return error_response(
            "timeout", url, f"Timeout fetching {url}",
            retry_eligible=True,          # Coordinator CAN retry
        )
    except WebSearchNotFoundError:
        return error_response(
            "not_found", url, f"Page not found: {url}",
            fallback_available=True,      # Don't retry 404s; try a different source
        )
```

Three important patterns here:

1. **Input validation returns structured errors**, not exceptions. Missing URL is `invalid_input` with `retry_eligible=False`.
2. **Timeout errors are retry-eligible**. The coordinator can try again.
3. **Not-found errors have fallback available**. The coordinator should try a different source instead.

This gives the coordinator a **decision tree** for every failure mode. Compare this to the silent failure anti-pattern (Section 14) where the coordinator gets `{"status":"success","data":null}` and cannot tell what happened.

---

## 7. The Agent Loop -- Stop-Reason-Driven Execution

**File:** `src/research_agents/agent/agent_loop.py`

### AgentResult and UsageSummary

```python
@dataclass
class UsageSummary:
    input_tokens: int = 0
    output_tokens: int = 0

    def add(self, usage: dict) -> None:
        self.input_tokens += usage.get("input_tokens", 0)
        self.output_tokens += usage.get("output_tokens", 0)

@dataclass
class AgentResult:
    content: str                                          # final text response
    messages: list[dict] = field(default_factory=list)    # full message history
    usage: UsageSummary = field(default_factory=UsageSummary)
    tool_calls: int = 0                                   # number of tool calls made
    iterations: int = 0                                   # number of loop iterations
    stop_reason: str = ""          # last API stop_reason, or "max_iterations" if cut off
    tool_results: list[dict] = field(default_factory=list)  # {"tool_name", "tool_input", "result"}
```

`AgentResult` captures everything the coordinator needs from a subagent run: the final text content, usage metrics, the full message history, why the loop stopped, and a structured log of every tool call with the JSON string the handler returned. That log is what `collect_gaps()` reads (Section 10): a subagent that writes a confident summary after a timed-out fetch cannot hide the timeout, because the coordinator reads the tool result, not the prose.

### The Loop: run_agent_loop()

```python
def run_agent_loop(
    client: object,
    services: ServiceContainer,
    user_message: str,
    system_prompt: str,
    tools: list[dict],
    agent_type: str,
    model: str = "claude-sonnet-4-6",
    max_iterations: int = 10,
    dispatch_fn: DispatchFn = dispatch,
) -> AgentResult:
    messages = [{"role": "user", "content": user_message}]
    result = AgentResult(content="")

    for _ in range(max_iterations):
        result.iterations += 1
        response = client.messages.create(
            model=model, max_tokens=4096,
            system=system_prompt, tools=tools, messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})
        result.stop_reason = response.stop_reason

        # Stop-reason driven control flow
        if response.stop_reason != "tool_use":
            # end_turn, max_tokens, stop_sequence, refusal, pause_turn, ...:
            # extract any text and stop
            ...
            return result

        # tool_use: dispatch each call via dispatch_fn, log it in
        # result.tool_results, append a tool_result block with is_error set
        # when the handler returned status == "error", then continue
        ...

    result.stop_reason = "max_iterations"
    return result
```

Key CCA pattern: **Stop-reason-driven loop**. Control flow branches on `response.stop_reason`: `tool_use` dispatches tools and continues; every other stop reason (`end_turn`, `max_tokens`, `refusal`, `pause_turn`, ...) extracts text and exits. Block types are read only when *extracting* text or tool calls from a response, never to decide what to do next. Each `tool_result` block carries `is_error: true` when the handler returned a structured error, which is the Messages API's own signal for a failed tool call.

The `user_message` parameter receives the output of `build_subagent_context()` -- a plain string containing only explicitly-selected context. The coordinator's message history is never passed here.

The `tools` parameter receives the scoped tool list from `SubagentConfig.tools` -- 4 tools, not 20.

The `max_iterations` parameter is a safety limit to prevent runaway loops. If the agent makes 10 iterations without stopping, the loop exits with `stop_reason="max_iterations"`, and `collect_gaps()` reports that task as a gap rather than letting an empty result vanish from the report.

The `dispatch_fn` parameter defaults to the scoped `dispatch` and exists so a notebook can replay one transcript through a different router. It is the seam that makes the anti-patterns runnable.

---

## 8. Context Isolation -- The Enforcer

**File:** `src/research_agents/agent/context_builder.py`

This is the most important module for understanding the CCA context management pattern.

```python
def build_subagent_context(
    task: SubTask,
    predecessor_results: dict[str, AgentResult] | None = None,
) -> str:
```

The function signature is the enforcement mechanism. Notice what is **not** a parameter:
- The coordinator's `messages` list
- The coordinator's `system_prompt`
- Other subagents' results (the full dict)
- The original `ResearchQuery`

The subagent receives:
1. **`task.instruction`** -- what to do (always present)
2. **`task.context`** -- explicitly selected facts from the coordinator
3. **Predecessor results** -- filtered to only `task.depends_on` task IDs

```python
def build_subagent_context(task, predecessor_results=None) -> str:
    parts = []

    # 1. Task instruction (always present)
    parts.append(f"## Task\n{task.instruction}")

    # 2. Explicit context from coordinator (may be empty)
    if task.context:
        parts.append(f"## Context\n{task.context}")

    # 3. Predecessor results (only from depends_on tasks)
    if predecessor_results and task.depends_on:
        predecessor_parts = []
        for dep_id in task.depends_on:
            dep_result = predecessor_results.get(dep_id)
            if dep_result and dep_result.content:
                predecessor_parts.append(
                    f"### Results from {dep_id}\n{dep_result.content}"
                )
        if predecessor_parts:
            parts.append("## Prior Results\n" + "\n\n".join(predecessor_parts))

    return "\n\n".join(parts)
```

The output is a plain string with markdown headers. The subagent sees a clean, structured context with only the information the coordinator deliberately included.

### Why This Matters for the CCA Exam

When the exam asks "the subagent produced results that contradicted the coordinator's instructions," the answer is always that the instructions were in the coordinator's context but never explicitly forwarded. `build_subagent_context()` is the only way `run_coordinator()` builds subagent input, so inside the coordinator the leak cannot happen accidentally -- you would have to deliberately put coordinator-only information into the `SubTask.context` field. (`run_agent_loop()` itself accepts any string as `user_message`; that is the door the shared-context anti-pattern in Section 13 walks through.)

The cut goes both ways. If the coordinator *forgets* to copy a rule such as "use APA citations" into `task.context`, the subagent never sees it and no error is raised. Notebook 02 runs that case through the loop and shows the sent message has no citation instruction; that is the exam's "subagent returned MLA" scenario in miniature.

---

## 9. Subagent Configuration -- System Prompts and Tool Sets

**File:** `src/research_agents/agent/subagents.py`

### SubagentConfig

```python
@dataclass(frozen=True)
class SubagentConfig:
    system_prompt: str
    tools: list[dict]
```

A frozen (immutable) configuration pairing a system prompt with a scoped tool list. Once created, you cannot modify the tools or prompt at runtime.

### The Config Registry

```python
SUBAGENT_CONFIGS: dict[str, SubagentConfig] = {
    "web_researcher": SubagentConfig(
        system_prompt=WEB_RESEARCHER_PROMPT,
        tools=WEB_RESEARCHER_TOOLS,
    ),
    "document_analyzer": SubagentConfig(...),
    "data_extractor": SubagentConfig(...),
    "fact_checker": SubagentConfig(...),
}
```

The coordinator looks up the config by `task.agent_type` and passes `config.tools` to `run_agent_loop()`. This is how tool scoping is enforced: each agent type is structurally limited to its 4 tools.

### System Prompt Design

Each system prompt follows a pattern:

1. **Role declaration**: "You are a specialized Web Researcher agent."
2. **Tool inventory**: "You have 4 tools: search_web, fetch_page, extract_text, summarize_source."
3. **Instructions**: Step-by-step workflow for this agent type.
4. **Negative bounds**: "You do NOT have access to documents, databases, or fact-checking tools."

The negative bounds in the system prompt mirror the negative bounds in tool descriptions. This is belt-and-suspenders: the tool list structurally prevents the agent from calling wrong tools, and the system prompt tells the agent not to try.

---

## 10. The Coordinator -- Hub-and-Spoke Orchestration

**File:** `src/research_agents/agent/coordinator.py`

### sort_tasks_into_waves()

```python
def sort_tasks_into_waves(tasks: list[SubTask]) -> list[list[SubTask]]:
    completed: set[str] = set()
    remaining = list(tasks)
    waves: list[list[SubTask]] = []

    while remaining:
        wave = [t for t in remaining
                if all(d in completed for d in t.depends_on)]
        if not wave:
            wave = remaining  # Circular dependency fallback
            remaining = []
        else:
            remaining = [t for t in remaining if t not in wave]
        waves.append(wave)
        completed.update(t.task_id for t in wave)

    return waves
```

Topological sort into parallel execution waves. Each iteration finds all tasks whose dependencies are already satisfied. The circular dependency fallback puts everything in one wave rather than deadlocking.

### run_coordinator()

```python
def run_coordinator(
    client: object,
    services: ServiceContainer,
    tasks: list[SubTask],
    model: str = "claude-sonnet-4-6",
    max_iterations: int = 10,
    dispatch_fn: DispatchFn = dispatch,
) -> tuple[dict[str, AgentResult], list[list[SubTask]]]:
    waves = sort_tasks_into_waves(tasks)
    results: dict[str, AgentResult] = {}

    for wave in waves:
        for task in wave:
            config = SUBAGENT_CONFIGS.get(task.agent_type)
            if config is None:
                results[task.task_id] = AgentResult(
                    content=f"Error: unknown agent_type '{task.agent_type}'"
                )
                continue

            # Context isolation enforced HERE
            context_string = build_subagent_context(task, predecessor_results=results)

            # Run with scoped tools
            result = run_agent_loop(
                client=client, services=services,
                user_message=context_string,
                system_prompt=config.system_prompt,
                tools=config.tools,
                agent_type=task.agent_type, model=model,
                max_iterations=max_iterations, dispatch_fn=dispatch_fn,
            )
            results[task.task_id] = result

    return results, waves
```

This function executes Steps 2-3 of the 6-step flow. For each task:
1. Look up the `SubagentConfig` (system prompt + tools)
2. Build explicit context via `build_subagent_context()`
3. Run the agent loop with scoped tools

The `predecessor_results=results` parameter means tasks in Wave 1+ can access results from earlier waves, but only for the specific task IDs listed in `depends_on`. Tasks inside a wave are independent but are executed one after another; "parallel" describes the dependency structure, not concurrency.

Two of the six steps have no code of their own. **PLAN** (step 1) is done by the caller, who writes the `SubTask` list; the package contains no query-decomposition code. **EVALUATE** (step 4) is a `fact_checker` SubTask that `depends_on` the others, so its `verify_claim` and `flag_conflict` tool results are what the coordinator feeds to RESOLVE.

### collect_tool_errors() and collect_gaps()

```python
def collect_tool_errors(results: dict[str, AgentResult]) -> list[dict]:
    # every tool result whose JSON has status == "error", with
    # task_id, tool_name, error_type, source, retry_eligible, fallback_available

def collect_gaps(results: dict[str, AgentResult]) -> list[str]:
    # "<source> (<error_type>)" per tool error, plus
    # "<task_id> (max_iterations)" for any subagent the loop cut off
```

This is where the structured-error guarantee becomes visible. Both functions walk `AgentResult.tool_results`, the loop's own log, never the model's text. A subagent whose summary says "fetched the dataset" after the fetch timed out still produces a gap, because the timeout is in the log. Replace the router with `silent_dispatch` and the same transcript produces no gap at all: the handler said `success`, so there is nothing to collect. That is the silent-failure cascade, executed rather than described (Notebooks 04 and 08).

### build_research_report()

```python
def build_research_report(
    query: str,
    results: dict[str, AgentResult],
    reliability_lookup: dict[str, SourceReliability],
    conflicts: list[dict] | None = None,
    gaps: list[str] | None = None,
) -> ResearchReport:
```

Steps 5-6: resolve conflicts and compile the final report. When `gaps` is omitted it is derived with `collect_gaps(results)`. The confidence score starts at 0.8 and is reduced by gaps (-0.1 each) and unresolved human-flagged conflicts (-0.05 each), then rounded to two decimals. The minimum confidence is 0.1.

---

## 11. Conflict Resolution -- Deterministic Strategies

**File:** `src/research_agents/agent/conflict_resolver.py`

### The Three-Tier Strategy

```python
RELIABILITY_SCORES = {
    SourceReliability.HIGH: 3,
    SourceReliability.MEDIUM: 2,
    SourceReliability.LOW: 1,
    SourceReliability.UNKNOWN: 0,
}
```

```python
def _best_tier(sources: list[str], reliability_lookup: dict[str, SourceReliability]) -> int:
    return max(
        (RELIABILITY_SCORES[match_reliability(src, reliability_lookup)] for src in sources),
        default=0,
    )
```

**Strategy 1: Source reliability ranking.** Compare the *best* tier on each side. The side whose most reliable source sits higher wins, so three blogs (best tier LOW) never outrank one `.gov` (best tier HIGH). Confidence scales with the tier gap:

```python
gap = abs(for_tier - against_tier)          # 1, 2 or 3
confidence = min(0.95, 0.5 + gap * 0.15)    # HIGH vs LOW: gap 2 -> 0.80
winning_side = "for" if for_tier > against_tier else "against"
```

**Strategy 2: Majority consensus.** If the best tiers tie, the side with more sources wins:

```python
confidence = min(0.85, majority_size / total)   # 3 of 4 -> 0.75
```

**Strategy 3: Flag for human review.** If both tier and count tie:

```python
resolution = "flagged_for_human"
confidence = 0.3
winning_side = "undecided"
```

This is **programmatic enforcement** -- the same inputs always produce the same output, and the output does not depend on the order the sources arrived in. No LLM reasoning is involved. This is the CCA principle that code-enforced rules beat prompt-based guidance.

### Batch Resolution

```python
def resolve_conflicts(
    conflicts: list[dict],
    reliability_lookup: dict[str, SourceReliability],
) -> list[ConflictRecord]:
```

Processes all conflicts in a batch. Each conflict dict has `claim`, `sources_for`, and `sources_against`; missing keys default rather than raise, so a malformed conflict cannot crash `build_research_report()`. Returns a list of `ConflictRecord` objects with resolution metadata.

---

## 12. Anti-Pattern 1: Super Agent (18+ Tools)

**File:** `src/research_agents/anti_patterns/super_agent.py`

```python
SUPER_AGENT_TOOLS = (
    WEB_RESEARCHER_TOOLS
    + DOCUMENT_ANALYZER_TOOLS
    + DATA_EXTRACTOR_TOOLS
    + FACT_CHECKER_TOOLS
    + COORDINATOR_TOOLS
)
```

All 20 tools on one agent. The super agent prompt is equally vague:

```python
SUPER_AGENT_PROMPT = """
You are a universal research agent. You have access to ALL tools:
web search, document parsing, data extraction, fact checking, and coordination.
Use whatever tools you need to answer the research query.
"""
```

```python
def super_agent_dispatch(agent_type, tool_name, input_dict, services) -> str:
    # agent_type is ignored: any caller can run any of the 20 tools
    handler = SUPER_AGENT_DISPATCH.get(tool_name)
    ...
```

`super_agent_dispatch` has the same signature as the scoped `dispatch`, so a notebook can inject it into `run_agent_loop()`. Notebook 03 replays one scripted `query_database` call from a web researcher through both: the super agent returns database rows, the scoped router returns a structured `invalid_input` error.

### Why This Fails

When an agent has 18+ tools (20 here):
- A significant portion of attention goes to evaluating tool descriptions instead of the actual task
- Similar tools create ambiguity (e.g., `search_web` vs `cross_reference` -- both find information)
- The generic system prompt provides no workflow guidance

The first two are claims about model behaviour that this project cannot measure without a live model. What it *can* show is the structural half: with a flat tool map nothing in the code stops a wrong choice from executing, and with scoped dispatch the wrong choice is refused.

The CCA exam answer is always **"decompose into specialized subagents with 4-5 tools each."** The common distractors are:
- "improve tool descriptions" -- WRONG (doesn't fix the structural problem)
- "add a tool-selection preprocessing step" -- WRONG (adds complexity without addressing root cause)

---

## 13. Anti-Pattern 2: Shared Context (Leaky Coordinator)

**File:** `src/research_agents/anti_patterns/shared_context.py`

```python
def run_leaky_subagent(client, services, coordinator_messages, agent_type,
                       model="claude-sonnet-4-6") -> AgentResult:
    config = SUBAGENT_CONFIGS.get(agent_type)
    # WRONG: dumps entire coordinator history as the user message
    leaked_context = str(coordinator_messages)
    return run_agent_loop(
        client=client, services=services,
        user_message=leaked_context,  # ANTI-PATTERN
        system_prompt=config.system_prompt,
        tools=config.tools, agent_type=agent_type, model=model,
    )
```

The function takes the coordinator's full `messages` list as a parameter and converts it to a string. Problems:

1. **Token waste**: The subagent processes the entire coordinator conversation
2. **Context pollution**: A web researcher sees document analysis instructions
3. **Attention dilution**: Useful context is buried in irrelevant messages
4. **No isolation**: The subagent sees other subagents' results

Compare with `build_subagent_context()`, which structurally prevents this by not accepting the coordinator's messages as a parameter.

Notebook 02 runs this function through the loop with a recording client and reads back `client.calls[0]["messages"][0]["content"]`, the message the subagent was actually sent. For a three-message coordinator history it is a 358-character Python `repr` that contains the coordinator's planning and another subagent's tool result; the explicit version of the same task is 154 characters and contains neither.

---

## 14. Anti-Pattern 3: Silent Failures

**File:** `src/research_agents/anti_patterns/silent_failures.py`

```python
def handle_fetch_page_silent(input_dict, services) -> str:
    try:
        page = services.web_search.fetch_page(input_dict.get("url", ""))
        return json.dumps({"status": "success", "data": page.model_dump()})
    except (WebSearchTimeoutError, WebSearchNotFoundError):
        return json.dumps({"status": "success", "data": None})  # SILENT FAILURE
    except Exception:
        return json.dumps({"status": "success", "data": None})  # SILENT FAILURE
```

Returns `{"status": "success", "data": null}` on every error. The coordinator cannot distinguish between:
- "no relevant data exists" (legitimate empty result)
- "the subagent failed to retrieve data" (error that needs handling)

This creates **systematic bias** in the final report -- it reflects only the sources that happened to be available, not the full picture. The report's confidence score is falsely high because it doesn't know about the gaps.

```python
def silent_dispatch(agent_type, tool_name, input_dict, services) -> str:
    # silent handlers for search_web / fetch_page, the real dispatch for everything else
```

`silent_dispatch` lets the cascade be executed rather than described. Notebooks 04 and 08 run one scripted transcript (a web researcher that fetches the timeout URL and then writes a confident summary) through `run_coordinator()` twice. Through `dispatch` the report says `gaps=['https://timeout.example.com/remote-data (timeout)']` with confidence 0.70; through `silent_dispatch` it says `gaps=[]` with confidence 0.80. The model's prose is identical in both runs.

The correct pattern (Section 6) returns structured error context with `error_type`, `retry_eligible`, `fallback_available`, and `partial_data`, giving the coordinator the information it needs to make informed decisions.

---

## 15. MCP Primitives -- Tools, Resources, and Prompts

MCP (Model Context Protocol) defines three server primitives. The specification's strongest classification tell is *who decides to use each one*:

| Primitive | Controlled by | Meaning |
|-----------|---------------|---------|
| **Prompts** | User | Exposed for the user to pick explicitly (slash commands, menus) |
| **Resources** | Application | The host application decides what context to attach for the model |
| **Tools** | Model | The model decides to call them, subject to human approval |

Resources are identified by URIs. The scheme is the server's choice (`file://`, `https://`, or a custom one such as `kb://`), and the client reads one with `resources/read`. There is no special `resource://` scheme.

### Tools (Verbs) -- Things the Agent Does

Actions the agent can invoke. In our system, these are the tool definitions in `definitions.py`:

| Tool | Agent | Action |
|------|-------|--------|
| `search_web(query)` | Web Researcher | Searches the web |
| `verify_claim(claim)` | Fact Checker | Checks a claim against knowledge base |
| `delegate_task(...)` | Coordinator | Delegates to a subagent |

### Resources (Nouns) -- Things the Agent Reads

Data schemas and catalogs. In our system, these would be MCP Resources if we used the protocol:

| Resource | Maps to | Data |
|----------|---------|------|
| `source_reliability_db` | `KnowledgeBase.get_source_reliability()` | URL -> reliability rating |
| `document_catalog` | `DocumentStore.list_documents()` | Available document metadata |
| `database_schemas` | `DatabaseService.get_schema()` | Table column definitions |

Resources are **read-only data**. The key distinction from Tools: Resources have no side effects and perform no computation.

### Prompts (Patterns) -- Templates the Agent Uses

Reusable message templates. In our system:

| Prompt | Maps to | Purpose |
|--------|---------|---------|
| Research query template | System prompts in `subagents.py` | Standardized agent behavior |
| Citation format template | Would be an MCP Prompt | Configurable citation styles |
| Error report template | `ToolErrorResponse` model | Structured error format |

### The CCA Exam Distinction

The most common exam mistake is classifying a **Resource** as a **Tool** because both involve "getting information." The difference:
- **Tools** perform actions or computation (verbs); the model decides to call them
- **Resources** are read-only data catalogs (nouns); the application decides to attach them
- **Prompts** are parameterized templates (patterns); the user decides to invoke them

If a question describes a source reliability database -> **Resource**, not a Tool.
If it describes a function that verifies a claim -> **Tool**.

---

## 16. How the Pieces Connect -- End-to-End Data Flow

Here's the complete flow for the `economic_impact` scenario, exactly as Notebook 08 executes it with scripted transcripts:

```
ResearchQuery("What is the economic impact of remote work on productivity?")
  |
  v
1. PLAN: The caller decomposes into 4 SubTasks
  |  web (web_researcher) -- no depends_on
  |  data (data_extractor) -- no depends_on
  |  docs (document_analyzer) -- no depends_on
  |  facts (fact_checker) -- depends_on: [web, data, docs]
  |
  v
2. SORT: sort_tasks_into_waves()
  |  Wave 0: [web, data, docs]  -- parallel
  |  Wave 1: [facts]            -- sequential
  |
  v
3. DELEGATE: For each task in each wave:
  |  a. SUBAGENT_CONFIGS[task.agent_type] -> SubagentConfig
  |  b. build_subagent_context(task, results) -> plain string
  |  c. run_agent_loop(client, services, context, prompt, tools, dispatch_fn=dispatch)
  |  d. dispatch(agent_type, tool_name, input, services), logged in tool_results
  |
  |  Wave 0 transcripts:
  |    web:  search_web("remote work economic impact on productivity") -> 4 results
  |          fetch_page("https://timeout.example.com/remote-data") -> TIMEOUT (structured error)
  |          (the model then writes a confident summary anyway)
  |    data: query_database("remote_work_stats") -> 5 rows (2020-2024)
  |    docs: parse_document("doc-remote-work-stanford") -> 2 sections + claims
  |
  |  Wave 1 transcript, with Wave 0 results in its context:
  |    facts: verify_claim("Remote workers are 20% less productive") -> verified=False
  |           flag_conflict("Remote workers are more productive",
  |                         for=[mckinsey.com, bls.gov], against=[workfromhome-blog])
  |
  v
4. EVALUATE: read from the logs, not the prose
  |  - conflicts: the fact checker's flag_conflict tool result
  |  - collect_tool_errors(results): [{task_id: web, tool_name: fetch_page,
  |                                    error_type: timeout, retry_eligible: True}]
  |  - collect_gaps(results): ["https://timeout.example.com/remote-data (timeout)"]
  |
  v
5. RESOLVE: resolve_conflicts(conflicts, SOURCE_RELIABILITY_RATINGS)
  |  Claim: "Remote workers are more productive"
  |  Best tier for:     bls.gov (HIGH=3)
  |  Best tier against: workfromhome-blog.example.com (LOW=1)
  |  Resolution: highest_reliability, winning_side=for, confidence=0.80 (gap 2)
  |
  v
6. SYNTHESIZE: build_research_report()
     ResearchReport(
       query="What is the economic impact...",
       findings=[4 SourceResults, one per subagent transcript],
       conflicts=[1 ConflictRecord: highest_reliability, winning_side="for"],
       gaps=["https://timeout.example.com/remote-data (timeout)"],
       confidence_score=0.70  (0.8 base - 0.1 for gap)
     )
```

Replay the same transcripts with `dispatch_fn=silent_dispatch` and the only lines that change are step 4's (no errors, no gaps) and the final confidence (0.80). Every step maps to a specific module, model, and CCA concept. The final report is transparent about what it found, what contradicted, what it couldn't reach, and how confident it is.

---

## Summary: CCA Exam Mapping

| CCA Exam Concept | Module | Anti-Pattern | Exam Question Pattern |
|------------------|--------|--------------|----------------------|
| Hub-and-spoke | `coordinator.py` | N/A | "What architecture for multi-agent?" -> single coordinator delegating |
| Context isolation | `context_builder.py` | `shared_context.py` | "Subagent ignores instructions" -> context not explicitly passed |
| Tool scoping (4-5) | `definitions.py` | `super_agent.py` | "Agent picks wrong tool" -> decompose into 4-5 tools per agent |
| Structured errors | `ToolErrorResponse` | `silent_failures.py` | "Report missing data" -> require structured error context |
| Conflict resolution | `conflict_resolver.py` | First-result-wins (Notebook 06) | "Contradicting sources" -> best-tier reliability ranking, then majority, then human flag |
| Task decomposition | `sort_tasks_into_waves()` | All-sequential | "Parallel or sequential?" -> check data dependencies |
| MCP primitives | Notebook 07 | N/A | "Source reliability DB" -> Resource, not Tool |
