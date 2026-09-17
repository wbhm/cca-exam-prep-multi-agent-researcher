"""Core agentic tool-use loop reusable by every subagent.

Mirrors the sibling project's agent_loop.py pattern:
- Control flow branches on ``response.stop_reason``, never on which content
  block types happen to be present. (Block types are still read when
  *extracting* text or tool calls from a response.)
- Returns an AgentResult dataclass with content, usage, stop reason and a
  structured log of every tool call and its JSON result.
- Max iterations safety limit; exhausting it is recorded, not hidden.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field

from research_agents.services.container import ServiceContainer
from research_agents.tools.handlers import dispatch

DispatchFn = Callable[[str, str, dict, ServiceContainer], str]


@dataclass
class UsageSummary:
    """Token usage accumulated across all loop iterations."""

    input_tokens: int = 0
    output_tokens: int = 0

    def add(self, usage: dict) -> None:
        self.input_tokens += usage.get("input_tokens", 0)
        self.output_tokens += usage.get("output_tokens", 0)


@dataclass
class AgentResult:
    """Result from a single subagent run."""

    content: str  # final text response
    messages: list[dict] = field(default_factory=list)  # full message history
    usage: UsageSummary = field(default_factory=UsageSummary)
    tool_calls: int = 0  # number of tool calls made
    iterations: int = 0  # number of loop iterations
    stop_reason: str = ""  # last API stop_reason, or "max_iterations" if the loop was cut off
    # One entry per tool call: {"tool_name", "tool_input", "result"} with result the JSON string
    tool_results: list[dict] = field(default_factory=list)


def _extract_text(content: list) -> str:
    """First text block in a response, handling object- and dict-style blocks."""
    for block in content:
        if hasattr(block, "text"):
            return block.text
        if isinstance(block, dict) and block.get("type") == "text":
            return block["text"]
    return ""


def _is_error_result(tool_result: str) -> bool:
    """True when a handler's JSON says status == "error"."""
    try:
        return json.loads(tool_result).get("status") == "error"
    except (ValueError, AttributeError):
        return False


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
    """Run an agentic tool-use loop until the model stops or max iterations.

    This function makes actual API calls via the client. For testing,
    pass a mock client that returns pre-built responses (see
    ``research_agents.testing.scripted_client``).

    Args:
        client: Anthropic client (or mock)
        services: ServiceContainer for tool dispatch
        user_message: The explicit context string (NOT coordinator messages)
        system_prompt: Agent-specific system prompt
        tools: Scoped tool list (4-5 tools for this agent type)
        agent_type: Which agent type for dispatch routing
        model: Claude model ID
        max_iterations: Safety limit to prevent runaway loops
        dispatch_fn: Tool router; defaults to the scoped registry in
            ``tools.handlers``. Anti-pattern notebooks inject their own.

    Returns:
        AgentResult with final content, message history, usage, stop reason
        and the structured tool-call log.
    """
    messages: list[dict] = [{"role": "user", "content": user_message}]
    result = AgentResult(content="")
    result.messages = messages

    for _ in range(max_iterations):
        result.iterations += 1

        response = client.messages.create(  # type: ignore[union-attr]
            model=model,
            max_tokens=4096,
            system=system_prompt,
            tools=tools,
            messages=messages,
        )

        # Accumulate usage
        if hasattr(response, "usage"):
            usage_dict = (
                response.usage
                if isinstance(response.usage, dict)
                else {"input_tokens": getattr(response.usage, "input_tokens", 0),
                       "output_tokens": getattr(response.usage, "output_tokens", 0)}
            )
            result.usage.add(usage_dict)

        # Append assistant response to history
        messages.append({"role": "assistant", "content": response.content})
        result.stop_reason = response.stop_reason

        # Stop-reason driven control flow: only tool_use continues the loop.
        # end_turn, max_tokens, stop_sequence, refusal, pause_turn and any
        # future value all end the run with whatever text was produced.
        if response.stop_reason != "tool_use":
            result.content = _extract_text(response.content)
            return result

        # Dispatch each tool call
        tool_results = []
        for block in response.content:
            # Handle both object-style and dict-style blocks
            if hasattr(block, "type") and block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input if isinstance(block.input, dict) else {}
                tool_id = block.id
            elif isinstance(block, dict) and block.get("type") == "tool_use":
                tool_name = block["name"]
                tool_input = block.get("input", {})
                tool_id = block["id"]
            else:
                continue

            result.tool_calls += 1
            tool_result = dispatch_fn(agent_type, tool_name, tool_input, services)
            result.tool_results.append({
                "tool_name": tool_name,
                "tool_input": tool_input,
                "result": tool_result,
            })

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": tool_result,
                "is_error": _is_error_result(tool_result),
            })

        messages.append({"role": "user", "content": tool_results})

    result.stop_reason = "max_iterations"
    return result
