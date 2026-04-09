"""Pre-built simulated data for all services.

Includes sources with contradicting claims (for conflict resolution),
URLs that timeout (for error handling), and multiple reliability levels.
All data is deterministic for reproducible notebook demos.
"""

from __future__ import annotations

from research_agents.models.research import (
    Document,
    DocumentSection,
    FactRecord,
    PageContent,
    SearchResult,
    SourceReliability,
)

# ---------------------------------------------------------------------------
# Web Search: search index (keyword -> results) and page content
# ---------------------------------------------------------------------------

SEARCH_INDEX: dict[str, list[SearchResult]] = {
    "renewable energy": [
        SearchResult(
            url="https://energy.gov/renewable-2024",
            title="Global Renewable Energy Report 2024",
            snippet="Renewable energy now accounts for 30% of global electricity generation.",
            reliability=SourceReliability.HIGH,
        ),
        SearchResult(
            url="https://reuters.com/energy-transition",
            title="Energy Transition Accelerates",
            snippet="Investment in renewables reached $500 billion in 2024.",
            reliability=SourceReliability.MEDIUM,
        ),
        SearchResult(
            url="https://energyblog.example.com/renewables",
            title="Why Renewables Will Dominate by 2030",
            snippet="Renewable energy accounts for 45% of global electricity.",  # Contradicts .gov
            reliability=SourceReliability.LOW,
        ),
    ],
    "ai healthcare": [
        SearchResult(
            url="https://nih.gov/ai-diagnostics-2024",
            title="AI in Medical Diagnostics: NIH Review",
            snippet="AI-assisted diagnostics show 94% accuracy in radiology screening.",
            reliability=SourceReliability.HIGH,
        ),
        SearchResult(
            url="https://nature.com/ai-pathology",
            title="Deep Learning for Pathology",
            snippet="CNN-based systems match expert pathologists in cancer detection.",
            reliability=SourceReliability.HIGH,
        ),
        SearchResult(
            url="https://healthtech.example.com/ai-revolution",
            title="AI Revolution in Healthcare",
            snippet="Every hospital will use AI diagnostics by 2025.",
            reliability=SourceReliability.LOW,
        ),
    ],
    "remote work economic": [
        SearchResult(
            url="https://bls.gov/remote-work-stats",
            title="Remote Work Statistics 2024",
            snippet="27.6% of US employees work remotely at least part-time.",
            reliability=SourceReliability.HIGH,
        ),
        SearchResult(
            url="https://mckinsey.com/future-of-work",
            title="The Future of Remote Work",
            snippet="Remote work increases productivity by 13% on average.",
            reliability=SourceReliability.MEDIUM,
        ),
        SearchResult(
            url="https://workfromhome-blog.example.com/productivity",
            title="Remote Work Kills Productivity",
            snippet="Studies show remote workers are 20% less productive.",  # Contradicts McKinsey
            reliability=SourceReliability.LOW,
        ),
        SearchResult(
            url="https://timeout.example.com/remote-data",
            title="Comprehensive Remote Work Data",
            snippet="The most complete dataset on remote work outcomes.",
            reliability=SourceReliability.MEDIUM,
        ),
    ],
}

PAGE_CONTENT: dict[str, PageContent] = {
    "https://energy.gov/renewable-2024": PageContent(
        url="https://energy.gov/renewable-2024",
        title="Global Renewable Energy Report 2024",
        text=(
            "According to the International Energy Agency, renewable energy sources "
            "accounted for approximately 30% of global electricity generation in 2024. "
            "Solar and wind combined grew 15% year-over-year. Investment in renewable "
            "infrastructure reached $495 billion, a new record. Key challenges remain "
            "in grid storage and transmission capacity."
        ),
        reliability=SourceReliability.HIGH,
    ),
    "https://reuters.com/energy-transition": PageContent(
        url="https://reuters.com/energy-transition",
        title="Energy Transition Accelerates",
        text=(
            "Global investment in the energy transition topped $500 billion in 2024, "
            "driven by falling costs of solar panels and battery storage. China leads "
            "with 40% of global renewable capacity additions. Europe follows with "
            "ambitious 2030 targets. Fossil fuel investment remains flat."
        ),
        reliability=SourceReliability.MEDIUM,
    ),
    "https://energyblog.example.com/renewables": PageContent(
        url="https://energyblog.example.com/renewables",
        title="Why Renewables Will Dominate by 2030",
        text=(
            "Renewable energy already provides 45% of global electricity — and that "
            "number is climbing fast. By 2030, fossil fuels will be irrelevant. "
            "The transition is happening faster than anyone predicted."
        ),
        reliability=SourceReliability.LOW,
    ),
    "https://nih.gov/ai-diagnostics-2024": PageContent(
        url="https://nih.gov/ai-diagnostics-2024",
        title="AI in Medical Diagnostics: NIH Review",
        text=(
            "A systematic review of 142 studies found AI-assisted diagnostic tools "
            "achieve 94% accuracy in radiology screening, compared to 88% for "
            "unassisted radiologists. The greatest improvements appear in early "
            "detection of lung cancer and diabetic retinopathy."
        ),
        reliability=SourceReliability.HIGH,
    ),
    "https://nature.com/ai-pathology": PageContent(
        url="https://nature.com/ai-pathology",
        title="Deep Learning for Pathology",
        text=(
            "Convolutional neural network systems now match the diagnostic accuracy "
            "of expert pathologists for common cancer types. In a blinded trial of "
            "10,000 samples, the AI system achieved 96.1% accuracy vs 96.3% for "
            "a panel of three expert pathologists."
        ),
        reliability=SourceReliability.HIGH,
    ),
    "https://bls.gov/remote-work-stats": PageContent(
        url="https://bls.gov/remote-work-stats",
        title="Remote Work Statistics 2024",
        text=(
            "The Bureau of Labor Statistics reports that 27.6% of US employees "
            "worked remotely at least part-time in 2024. Hybrid arrangements "
            "are most common (18.2%), followed by fully remote (9.4%). "
            "Technology and financial services lead adoption."
        ),
        reliability=SourceReliability.HIGH,
    ),
    "https://mckinsey.com/future-of-work": PageContent(
        url="https://mckinsey.com/future-of-work",
        title="The Future of Remote Work",
        text=(
            "McKinsey's analysis of 800 companies found remote workers are 13% "
            "more productive on average, with significant variation by role type. "
            "Knowledge workers show the greatest gains (+22%), while collaborative "
            "roles show smaller improvements (+5%)."
        ),
        reliability=SourceReliability.MEDIUM,
    ),
    "https://workfromhome-blog.example.com/productivity": PageContent(
        url="https://workfromhome-blog.example.com/productivity",
        title="Remote Work Kills Productivity",
        text=(
            "Despite what big companies claim, remote work makes people 20% less "
            "productive. My survey of 50 freelancers showed most struggle with "
            "distraction and isolation. The office is where real work happens."
        ),
        reliability=SourceReliability.LOW,
    ),
}

# URLs that intentionally fail (for error handling demos)
TIMEOUT_URLS: set[str] = {
    "https://timeout.example.com/remote-data",
}

NOT_FOUND_URLS: set[str] = {
    "https://healthtech.example.com/ai-revolution",
}

# ---------------------------------------------------------------------------
# Document Store: research documents with sections and claims
# ---------------------------------------------------------------------------

DOCUMENTS: dict[str, Document] = {
    "doc-renewable-iea": Document(
        doc_id="doc-renewable-iea",
        title="IEA World Energy Outlook 2024",
        sections=[
            DocumentSection(
                heading="Executive Summary",
                content="Renewable energy capacity grew 50% in 2024.",
                claims=["Renewable capacity grew 50% in 2024"],
            ),
            DocumentSection(
                heading="Solar Energy",
                content="Solar PV installations reached 420 GW in 2024.",
                claims=["Solar PV installations reached 420 GW"],
            ),
            DocumentSection(
                heading="Investment Trends",
                content="Global clean energy investment was $1.8 trillion in 2024.",
                claims=["Clean energy investment was $1.8 trillion"],
            ),
        ],
        citations=["IEA World Energy Outlook 2024", "IRENA Renewable Capacity Statistics"],
        reliability=SourceReliability.HIGH,
    ),
    "doc-ai-health-review": Document(
        doc_id="doc-ai-health-review",
        title="Systematic Review: AI in Clinical Medicine",
        sections=[
            DocumentSection(
                heading="Methodology",
                content="Review of 142 peer-reviewed studies from 2020-2024.",
                claims=[],
            ),
            DocumentSection(
                heading="Diagnostic Accuracy",
                content="AI achieves 94% diagnostic accuracy across imaging modalities.",
                claims=["AI achieves 94% diagnostic accuracy"],
            ),
            DocumentSection(
                heading="Limitations",
                content="Most studies lack external validation and real-world deployment data.",
                claims=["Most AI diagnostic studies lack external validation"],
            ),
        ],
        citations=["NIH AI Diagnostics Review 2024", "Nature Medicine Vol. 30"],
        reliability=SourceReliability.HIGH,
    ),
    "doc-remote-work-stanford": Document(
        doc_id="doc-remote-work-stanford",
        title="Stanford Remote Work Study 2024",
        sections=[
            DocumentSection(
                heading="Key Findings",
                content="Hybrid workers show 13% higher productivity than office-only.",
                claims=["Hybrid workers are 13% more productive"],
            ),
            DocumentSection(
                heading="Employee Satisfaction",
                content="Remote workers report 24% higher job satisfaction.",
                claims=["Remote workers have 24% higher job satisfaction"],
            ),
        ],
        citations=["Bloom et al. 2024", "Stanford WFH Research"],
        reliability=SourceReliability.HIGH,
    ),
}

# ---------------------------------------------------------------------------
# Database: structured statistical data
# ---------------------------------------------------------------------------

DATABASE_TABLES: dict[str, list[dict]] = {
    "renewable_capacity": [
        {"year": 2020, "source": "solar", "capacity_gw": 710, "growth_pct": 22},
        {"year": 2020, "source": "wind", "capacity_gw": 743, "growth_pct": 18},
        {"year": 2022, "source": "solar", "capacity_gw": 1050, "growth_pct": 25},
        {"year": 2022, "source": "wind", "capacity_gw": 899, "growth_pct": 12},
        {"year": 2024, "source": "solar", "capacity_gw": 1580, "growth_pct": 30},
        {"year": 2024, "source": "wind", "capacity_gw": 1020, "growth_pct": 14},
    ],
    "remote_work_stats": [
        {"year": 2020, "remote_pct": 35.0, "hybrid_pct": 10.0, "office_pct": 55.0},
        {"year": 2021, "remote_pct": 28.0, "hybrid_pct": 18.0, "office_pct": 54.0},
        {"year": 2022, "remote_pct": 15.0, "hybrid_pct": 25.0, "office_pct": 60.0},
        {"year": 2023, "remote_pct": 11.0, "hybrid_pct": 20.0, "office_pct": 69.0},
        {"year": 2024, "remote_pct": 9.4, "hybrid_pct": 18.2, "office_pct": 72.4},
    ],
    "ai_healthcare_metrics": [
        {"modality": "radiology", "ai_accuracy": 94.0, "human_accuracy": 88.0, "studies": 45},
        {"modality": "pathology", "ai_accuracy": 96.1, "human_accuracy": 96.3, "studies": 28},
        {"modality": "dermatology", "ai_accuracy": 91.0, "human_accuracy": 87.0, "studies": 32},
        {"modality": "ophthalmology", "ai_accuracy": 95.5, "human_accuracy": 90.0, "studies": 37},
    ],
}

# ---------------------------------------------------------------------------
# Knowledge Base: verified facts and source reliability ratings
# ---------------------------------------------------------------------------

VERIFIED_FACTS: list[FactRecord] = [
    FactRecord(
        claim="Renewable energy accounts for 30% of global electricity",
        verified=True,
        confidence=0.95,
        source="IEA World Energy Outlook 2024",
        reliability=SourceReliability.HIGH,
    ),
    FactRecord(
        claim="Renewable energy accounts for 45% of global electricity",
        verified=False,
        confidence=0.10,
        source="Fact-check: no credible source supports 45%",
        reliability=SourceReliability.HIGH,
    ),
    FactRecord(
        claim="AI achieves 94% diagnostic accuracy in radiology",
        verified=True,
        confidence=0.90,
        source="NIH Systematic Review 2024",
        reliability=SourceReliability.HIGH,
    ),
    FactRecord(
        claim="Remote workers are 13% more productive",
        verified=True,
        confidence=0.80,
        source="Stanford/McKinsey studies 2024",
        reliability=SourceReliability.HIGH,
    ),
    FactRecord(
        claim="Remote workers are 20% less productive",
        verified=False,
        confidence=0.05,
        source="Fact-check: contradicts peer-reviewed evidence",
        reliability=SourceReliability.HIGH,
    ),
]

SOURCE_RELIABILITY_RATINGS: dict[str, SourceReliability] = {
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
