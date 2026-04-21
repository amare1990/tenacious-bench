from briefs.models import (
    CompanyProfile,
    HiringSignalBrief,
    AIMaturityProfile,
    CompetitorGapBrief,
    BenchMatchSummary
)


def get_mock_company():
    return CompanyProfile(
        company_name="Acme AI",
        industry="SaaS",
        employee_count=50,
        location="US",
        funding_stage="Series A",
        last_funding_date="2026-01"
    )


def get_mock_signals():
    return HiringSignalBrief(
        funding_signal="Raised $15M Series A recently",
        hiring_velocity_signal="Engineering roles doubled in last 60 days",
        layoffs_signal=None,
        leadership_change_signal="New CTO joined 2 months ago",
        tech_stack_signal="Uses Python, AWS",
        confidence_by_signal={
            "funding": 0.9,
            "hiring": 0.8,
            "leadership": 0.7
        },
        summary="Recently funded and rapidly scaling engineering team"
    )


def get_mock_ai_maturity():
    return AIMaturityProfile(
        score=2,
        evidence=["Hiring ML engineers", "Mentions AI in blog"],
        confidence=0.75,
        rationale="Moderate AI activity but not fully mature"
    )


def get_mock_gap():
    return CompetitorGapBrief(
        peer_group=["CompetitorA", "CompetitorB"],
        top_quartile_practices=["Dedicated ML platform", "Data infra automation"],
        missing_practices=["No ML platform team"],
        confidence=0.7,
        summary="Peers have stronger AI infrastructure capabilities"
    )


def get_mock_bench():
    return BenchMatchSummary(
        requested_capabilities=["Python", "ML"],
        available_capabilities=["Python", "ML"],
        fit=True,
        confidence=0.9,
        notes="Strong match with available engineers"
    )
