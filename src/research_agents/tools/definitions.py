"""Tool definitions for all 5 agent types.

CCA Key Concept: Each agent gets 4-5 focused tools. The super agent
anti-pattern (18+ tools) is in anti_patterns/super_agent.py.

Each tool description includes negative bounds ("does NOT...") to
prevent misrouting. This is the exam-correct approach — validation
inside the tool doesn't fix the routing problem.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Web Researcher: 4 tools
# ---------------------------------------------------------------------------

WEB_RESEARCHER_TOOLS: list[dict] = [
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
    },
    {
        "name": "fetch_page",
        "description": (
            "Fetch the full text content of a web page by URL. "
            "Returns the page title and extracted text. "
            "Does NOT perform search (use search_web first to find URLs). "
            "May fail with timeout or not-found errors."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL of the page to fetch"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "extract_text",
        "description": (
            "Extract and clean the main text content from a fetched page. "
            "Removes navigation, ads, and boilerplate. "
            "Does NOT parse structured documents (use parse_document for PDFs/reports)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL of the previously fetched page"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "summarize_source",
        "description": (
            "Create a brief summary of a web source including key claims and reliability. "
            "Does NOT verify claims (use verify_claim from fact_checker for that)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL of the source to summarize"},
            },
            "required": ["url"],
        },
    },
]

# ---------------------------------------------------------------------------
# Document Analyzer: 4 tools
# ---------------------------------------------------------------------------

DOCUMENT_ANALYZER_TOOLS: list[dict] = [
    {
        "name": "parse_document",
        "description": (
            "Parse a research document and return its structure (sections, headings). "
            "Works with document IDs from the document store. "
            "Does NOT work with web URLs (use fetch_page for web content)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "doc_id": {"type": "string", "description": "Document ID in the store"},
            },
            "required": ["doc_id"],
        },
    },
    {
        "name": "extract_sections",
        "description": (
            "Extract specific sections from a parsed document by heading. "
            "Returns section content and any claims within. "
            "Does NOT search across documents (use list_documents first)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "doc_id": {"type": "string", "description": "Document ID"},
                "heading": {
                    "type": "string",
                    "description": "Section heading to extract (partial match)",
                },
            },
            "required": ["doc_id"],
        },
    },
    {
        "name": "identify_claims",
        "description": (
            "Extract all factual claims from a document. "
            "Returns a list of claim strings that can be fact-checked. "
            "Does NOT verify claims (use verify_claim from fact_checker)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "doc_id": {"type": "string", "description": "Document ID"},
            },
            "required": ["doc_id"],
        },
    },
    {
        "name": "check_citations",
        "description": (
            "Verify that a document's citations are present and properly formatted. "
            "Returns citation list and any issues found. "
            "Does NOT verify the accuracy of cited content."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "doc_id": {"type": "string", "description": "Document ID"},
            },
            "required": ["doc_id"],
        },
    },
]

# ---------------------------------------------------------------------------
# Data Extractor: 4 tools
# ---------------------------------------------------------------------------

DATA_EXTRACTOR_TOOLS: list[dict] = [
    {
        "name": "query_database",
        "description": (
            "Query a named database table, optionally filtering by field values. "
            "Returns matching rows as a list of dictionaries. "
            "Does NOT search the web or documents (use search_web or parse_document)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Table name to query"},
                "filters": {
                    "type": "object",
                    "description": "Optional field-value filters (exact match)",
                },
            },
            "required": ["table"],
        },
    },
    {
        "name": "transform_data",
        "description": (
            "Transform query results by selecting columns and computing aggregates. "
            "Supports select, sum, average, count operations. "
            "Does NOT modify the underlying database."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Table name"},
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Columns to include",
                },
                "aggregate": {
                    "type": "string",
                    "enum": ["sum", "average", "count", "max", "min"],
                    "description": "Aggregate function to apply",
                },
                "aggregate_column": {
                    "type": "string",
                    "description": "Column to aggregate",
                },
            },
            "required": ["table"],
        },
    },
    {
        "name": "validate_schema",
        "description": (
            "Retrieve and validate the schema of a database table. "
            "Returns column names and types. "
            "Does NOT modify the schema."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Table name"},
            },
            "required": ["table"],
        },
    },
    {
        "name": "format_output",
        "description": (
            "Format query results as a structured summary for inclusion in reports. "
            "Converts raw data rows into a readable narrative. "
            "Does NOT perform analysis or draw conclusions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Table name"},
                "filters": {
                    "type": "object",
                    "description": "Optional filters to scope the data",
                },
            },
            "required": ["table"],
        },
    },
]

# ---------------------------------------------------------------------------
# Fact Checker: 4 tools
# ---------------------------------------------------------------------------

FACT_CHECKER_TOOLS: list[dict] = [
    {
        "name": "verify_claim",
        "description": (
            "Check a specific claim against the knowledge base of verified facts. "
            "Returns whether the claim is verified, with confidence score. "
            "Does NOT search the web (use search_web for finding sources)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "claim": {"type": "string", "description": "The factual claim to verify"},
            },
            "required": ["claim"],
        },
    },
    {
        "name": "cross_reference",
        "description": (
            "Cross-reference a claim across multiple sources to find agreements "
            "and contradictions. Returns sources that support or contradict. "
            "Does NOT resolve contradictions (the coordinator handles that)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "claim": {"type": "string", "description": "Claim to cross-reference"},
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Source URLs to check against",
                },
            },
            "required": ["claim"],
        },
    },
    {
        "name": "score_reliability",
        "description": (
            "Score the reliability of a source URL using the knowledge base. "
            "Returns HIGH, MEDIUM, LOW, or UNKNOWN. "
            "Does NOT fetch or analyze the source content."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Source URL to score"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "flag_conflict",
        "description": (
            "Flag a specific contradiction between sources for the coordinator. "
            "Records which sources agree and disagree on a claim. "
            "Does NOT resolve the conflict (the coordinator decides resolution)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "claim": {"type": "string", "description": "The disputed claim"},
                "sources_for": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Sources supporting the claim",
                },
                "sources_against": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Sources contradicting the claim",
                },
            },
            "required": ["claim", "sources_for", "sources_against"],
        },
    },
]

# ---------------------------------------------------------------------------
# Coordinator: 4 tools
# ---------------------------------------------------------------------------

COORDINATOR_TOOLS: list[dict] = [
    {
        "name": "delegate_task",
        "description": (
            "Delegate a subtask to a specialized subagent. "
            "Specify the agent type, instruction, and explicit context. "
            "The subagent receives ONLY what you pass here — it has no "
            "access to your conversation history or other subagent results. "
            "Does NOT execute the task itself (subagents do the work)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_type": {
                    "type": "string",
                    "enum": [
                        "web_researcher",
                        "document_analyzer",
                        "data_extractor",
                        "fact_checker",
                    ],
                    "description": "Which specialized agent to delegate to",
                },
                "instruction": {"type": "string", "description": "What the subagent should do"},
                "context": {
                    "type": "string",
                    "description": "Explicit context to pass (subagent sees ONLY this)",
                },
            },
            "required": ["agent_type", "instruction", "context"],
        },
    },
    {
        "name": "collect_results",
        "description": (
            "Collect and organize results from completed subagent tasks. "
            "Returns structured summaries of each subagent's findings. "
            "Does NOT execute any subagent tasks (use delegate_task first)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "IDs of completed tasks to collect",
                },
            },
            "required": ["task_ids"],
        },
    },
    {
        "name": "resolve_conflicts",
        "description": (
            "Resolve contradictions between subagent findings using "
            "source reliability ranking and majority consensus. "
            "Returns conflict records with resolution strategy. "
            "Does NOT collect results (use collect_results first)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "conflicts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "claim": {"type": "string"},
                            "sources_for": {"type": "array", "items": {"type": "string"}},
                            "sources_against": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                    "description": "List of conflicts to resolve",
                },
            },
            "required": ["conflicts"],
        },
    },
    {
        "name": "compile_report",
        "description": (
            "Compile all findings, resolved conflicts, and gaps into a "
            "final research report with confidence score. "
            "Does NOT perform research or verify facts (those are subagent tasks)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "findings_summary": {
                    "type": "string",
                    "description": "Synthesized findings from all subagents",
                },
                "conflicts": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Resolved conflict records",
                },
                "gaps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Sources that were unavailable",
                },
            },
            "required": ["findings_summary"],
        },
    },
]

# ---------------------------------------------------------------------------
# Convenience: all tool sets for iteration
# ---------------------------------------------------------------------------

ALL_TOOL_SETS: dict[str, list[dict]] = {
    "web_researcher": WEB_RESEARCHER_TOOLS,
    "document_analyzer": DOCUMENT_ANALYZER_TOOLS,
    "data_extractor": DATA_EXTRACTOR_TOOLS,
    "fact_checker": FACT_CHECKER_TOOLS,
    "coordinator": COORDINATOR_TOOLS,
}
