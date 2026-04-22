from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class CompanyProfile(BaseModel):
    company_name: str
    website: str | None = None
    industry: str | None = None
    employee_count: int | None = None
    location: str | None = None
    funding_stage: str | None = None
    last_funding_date: date | str | None = None
    slug: str | None = None
    source: str = "fixture"
    source_record_id: str | None = None
    source_paths: list[str] = Field(default_factory=list)
    raw_attributes: dict[str, Any] = Field(default_factory=dict)


class HiringSignalBrief(BaseModel):
    funding_signal: str | None = None
    hiring_velocity_signal: str | None = None
    layoffs_signal: str | None = None
    leadership_change_signal: str | None = None
    tech_stack_signal: str | None = None
    confidence_by_signal: dict[str, float] = Field(default_factory=dict)
    overall_summary: str | None = None
    funding_details: dict[str, Any] = Field(default_factory=dict)
    hiring_velocity_details: dict[str, Any] = Field(default_factory=dict)
    layoffs_details: dict[str, Any] = Field(default_factory=dict)
    leadership_change_details: dict[str, Any] = Field(default_factory=dict)
    tech_stack_details: dict[str, Any] = Field(default_factory=dict)
    source_paths: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)

    @property
    def summary(self) -> str | None:
        return self.overall_summary


class AIMaturityProfile(BaseModel):
    score: int = 0
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    rationale: str | None = None
    signal_breakdown: dict[str, Any] = Field(default_factory=dict)


class CompetitorGapBrief(BaseModel):
    peer_group: list[str] = Field(default_factory=list)
    top_quartile_practices: list[str] = Field(default_factory=list)
    missing_practices: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    summary: str | None = None
    sector: str | None = None
    company_size_band: str | None = None
    observed_practices: list[str] = Field(default_factory=list)


class BenchMatchSummary(BaseModel):
    requested_capabilities: list[str] = Field(default_factory=list)
    available_capabilities: list[str] = Field(default_factory=list)
    matched_capabilities: list[str] = Field(default_factory=list)
    fit: bool = False
    confidence: float = 0.0
    notes: str | None = None


class RawSourceStatus(BaseModel):
    source_name: str
    path: str
    present: bool
    populated: bool
    notes: str | None = None


class LeadRecord(BaseModel):
    company: CompanyProfile
    hiring_brief: HiringSignalBrief
    ai_profile: AIMaturityProfile
    competitor_gap: CompetitorGapBrief
    bench_match: BenchMatchSummary | None = None
    data_inventory: list[RawSourceStatus] = Field(default_factory=list)


class ConversationState(BaseModel):
    company_name: str
    channel: str = "email"
    stage: str = "outbound"
    last_outbound_message: str | None = None
    last_inbound_message: str | None = None
    next_action: str | None = None
    is_handoff_required: bool = False
    is_qualified: bool = False
    is_booked: bool = False


class ReplyAnalysis(BaseModel):
    reply_type: str
    confidence: float
    sentiment: str | None = None
    next_action: str | None = None
    reasoning: str | None = None
