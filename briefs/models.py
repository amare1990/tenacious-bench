from pydantic import BaseModel
from typing import List, Dict, Optional


class CompanyProfile(BaseModel):
    company_name: str
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    location: Optional[str] = None
    funding_stage: Optional[str] = None
    last_funding_date: Optional[str] = None


class HiringSignalBrief(BaseModel):
    funding_signal: Optional[str]
    hiring_velocity_signal: Optional[str]
    layoffs_signal: Optional[str]
    leadership_change_signal: Optional[str]
    tech_stack_signal: Optional[str]

    confidence_by_signal: Dict[str, float]
    summary: str


class AIMaturityProfile(BaseModel):
    score: int  # 0–3
    evidence: List[str]
    confidence: float
    rationale: str


class CompetitorGapBrief(BaseModel):
    peer_group: List[str]
    top_quartile_practices: List[str]
    missing_practices: List[str]
    confidence: float
    summary: str


class BenchMatchSummary(BaseModel):
    requested_capabilities: List[str]
    available_capabilities: List[str]
    fit: bool
    confidence: float
    notes: str


class LeadRecord(BaseModel):
    company_name: str
    segment: Optional[str]
    icp_confidence: float


class ConversationState(BaseModel):
    company_name: str
    channel: str
    stage: str
    last_outbound_message: Optional[str] = None
    last_inbound_message: Optional[str] = None
    next_action: Optional[str] = None
    is_handoff_required: bool = False
    is_qualified: bool = False
    is_booked: bool = False


class ReplyAnalysis(BaseModel):
    reply_type: str
    confidence: float
    sentiment: str
    next_action: str
    reasoning: str
