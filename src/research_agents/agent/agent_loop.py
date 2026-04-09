"""Core agentic tool-use loop reusable by every subagent.

Mirrors the sibling project's agent_loop.py pattern:
- Stop-reason driven (never checks content block types)
- Returns AgentResult dataclass with content + usage
- Max iterations safety limit
"""

from __future__ import annotations

from dataclasses import dataclass, field

from research_agents.services.container import ServiceContainer
from research_agents.tools.handlers import dispatch


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


def run_agent_loop(
    client: object,
    services: ServiceContainer,
    user_message: str,
    system_prompt: str,
    tools: list[dict],
    agent_type: str,
    model: str = "claude-sonnet-4-6",
    max_iterations: int = 10,
) -> AgentResult:
    """Run an agentic tool-use loop until end_turn or max iterations.

    This function makes actual API calls via the client. For testing,
    pass a mock client that returns pre-built responses.

    Args:
        client: Anthropic client (or mock)
        services: ServiceContainer for tool dispatch
        user_message: The explicit context string (NOT coordinator messages)
        system_prompt: Agent-specific system prompt
        tools: Scoped tool list (4-5 tools for this agent type)
        agent_type: Which agent type for dispatch routing
        model: Claude model ID
        max_iterations: Safety limit to prevent runaway loops

    Returns:
        AgentResult with final content, message history, and usage.
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

        # Stop-reason driven control flow (CCA Rule: never check content block types)
        if response.stop_reason == "end_turn":
            # Extract final text
            for block in response.content:
                if hasattr(block, "text"):
                    result.content = block.text
                    break
                elif isinstance(block, dict) and block.get("type") == "text":
                    result.content = block["text"]
                    break
            break

        if response.stop_reason == "tool_use":
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
                tool_result = dispatch(agent_type, tool_name, tool_input, services)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": tool_result,
                })

            messages.append({"role": "user", "content": tool_results})

    return result
