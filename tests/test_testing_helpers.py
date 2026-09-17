"""Tests for the scripted client shared by tests and notebooks."""

from __future__ import annotations

from research_agents.agent.agent_loop import run_agent_loop
from research_agents.agent.subagents import SUBAGENT_CONFIGS
from research_agents.services.container import ServiceContainer, make_default_services
from research_agents.testing import scripted_client, text_turn, tool_turn


def test_make_default_services_matches_fixture(services: ServiceContainer):
    made = make_default_services()
    assert made.knowledge_base.fact_count == services.knowledge_base.fact_count
    assert made.database.table_names == services.database.table_names


def test_scripted_client_records_every_call(services: ServiceContainer):
    client = scripted_client([tool_turn("search_web", {"query": "renewable energy"}),
                              text_turn("done")])
    result = run_agent_loop(
        client=client, services=services, user_message="hello",
        system_prompt="s", tools=[], agent_type="web_researcher",
    )
    assert result.content == "done"
    assert len(client.calls) == 2
    assert client.calls[0]["messages"][0]["content"] == "hello"
    assert client.calls[0]["system"] == "s"


def test_scripted_client_selects_transcript_by_agent(services: ServiceContainer):
    client = scripted_client({
        "web_researcher": [text_turn("web answer")],
        "data_extractor": [text_turn("data answer")],
    })
    web = run_agent_loop(
        client=client, services=services, user_message="q", system_prompt="s",
        tools=SUBAGENT_CONFIGS["web_researcher"].tools, agent_type="web_researcher",
    )
    data = run_agent_loop(
        client=client, services=services, user_message="q", system_prompt="s",
        tools=SUBAGENT_CONFIGS["data_extractor"].tools, agent_type="data_extractor",
    )
    assert (web.content, data.content) == ("web answer", "data answer")


def test_scripted_client_ends_turn_when_script_runs_out(services: ServiceContainer):
    client = scripted_client([])
    result = run_agent_loop(
        client=client, services=services, user_message="q",
        system_prompt="s", tools=[], agent_type="web_researcher",
    )
    assert result.stop_reason == "end_turn"
    assert result.iterations == 1
