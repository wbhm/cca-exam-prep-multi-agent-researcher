"""Scripted client for replaying fixed transcripts through the real loop.

No notebook or test in this project calls the Claude API. Instead a
transcript is scripted: each entry is the response the "model" gives on that
iteration, and ``run_agent_loop`` does everything else for real (dispatch,
tool results, message history, stop reasons). That makes every demonstration
deterministic and lets the same transcript be replayed through different
routers (scoped vs super-agent, structured vs silent) to isolate one variable.

Shared by ``tests/`` and the notebooks so there is one mock, not three.
"""

from __future__ import annotations

from itertools import count
from types import SimpleNamespace

from research_agents.tools.definitions import ALL_TOOL_SETS

_ids = count(1)

# First tool name in a scoped tool list -> agent type that owns it
_AGENT_BY_FIRST_TOOL: dict[str, str] = {
    tools[0]["name"]: agent_type for agent_type, tools in ALL_TOOL_SETS.items()
}


def text_turn(text: str, stop_reason: str = "end_turn") -> SimpleNamespace:
    """A response containing one text block."""
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        stop_reason=stop_reason,
        usage=SimpleNamespace(input_tokens=100, output_tokens=50),
    )


def tool_turn(name: str, input_dict: dict, tool_id: str | None = None) -> SimpleNamespace:
    """A response in which the model calls one tool."""
    return SimpleNamespace(
        content=[SimpleNamespace(
            type="tool_use",
            id=tool_id or f"call-{next(_ids)}",
            name=name,
            input=input_dict,
        )],
        stop_reason="tool_use",
        usage=SimpleNamespace(input_tokens=100, output_tokens=50),
    )


def agent_for_tools(tools: list[dict]) -> str:
    """Infer the agent type from a scoped tool list (by its first tool)."""
    if tools:
        return _AGENT_BY_FIRST_TOOL.get(tools[0].get("name", ""), "default")
    return "default"


Script = list[SimpleNamespace] | dict[str, list[SimpleNamespace]]


def scripted_client(script: Script) -> SimpleNamespace:
    """Build a client whose ``messages.create`` replays ``script``.

    Args:
        script: Either one list of responses (returned in order on every
            call) or a dict of lists keyed by agent type, selected per call
            from the ``tools`` kwarg. When a list is exhausted the client
            returns an ``end_turn`` text response so the loop always ends.

    The returned object records every ``create`` call's keyword arguments in
    ``client.calls`` so a caller can inspect exactly what the model was sent
    (``client.calls[0]["messages"][0]["content"]`` is the user message).
    """
    scripts: dict[str, list[SimpleNamespace]] = (
        {"default": list(script)} if isinstance(script, list)
        else {k: list(v) for k, v in script.items()}
    )
    cursors: dict[str, int] = {}
    calls: list[dict] = []

    def create(**kwargs) -> SimpleNamespace:
        calls.append(kwargs)
        key = agent_for_tools(kwargs.get("tools") or [])
        if key not in scripts:
            key = "default"
        turns = scripts.get(key, [])
        i = cursors.get(key, 0)
        cursors[key] = i + 1
        if i < len(turns):
            return turns[i]
        return text_turn("Analysis complete.")

    client = SimpleNamespace(messages=SimpleNamespace(create=create), calls=calls)
    return client


__all__: list[str] = ["scripted_client", "text_turn", "tool_turn", "agent_for_tools"]
