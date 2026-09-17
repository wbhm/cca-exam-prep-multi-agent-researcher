"""Shared test fixtures.

Creates a fresh ServiceContainer with seed data for every test.
No actual API calls are made — all services are simulated in-memory.
"""

from __future__ import annotations

import pytest

from research_agents.services.container import ServiceContainer, make_default_services


@pytest.fixture
def services() -> ServiceContainer:
    """Create a fresh ServiceContainer with all seed data."""
    return make_default_services()


def make_services() -> ServiceContainer:
    """Backwards-compatible alias; notebooks import make_default_services directly."""
    return make_default_services()
