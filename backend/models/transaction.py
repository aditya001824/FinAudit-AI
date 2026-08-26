"""
Data models for FinAudit AI - AML Forensic and Transaction Analysis System
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class Transaction(BaseModel):
    id: str = Field(..., description="Unique transaction ID")
    timestamp: str = Field(..., description="ISO timestamp of transaction")
    source_account: str = Field(..., description="Source account identifier")
    target_account: str = Field(..., description="Destination account identifier")
    source_entity: str = Field(..., description="Sender entity name")
    target_entity: str = Field(..., description="Receiver entity name")
    amount: float = Field(..., description="Transaction amount")
    currency: str = Field(default="USD", description="Currency code")
    transaction_type: str = Field(default="WIRE", description="WIRE, CASH_DEPOSIT, ACH, CRYPTO_SWAP, TRADE_INVOICE, SHELL_TRANSFER")
    source_country: str = Field(default="US", description="Origin country code")
    target_country: str = Field(default="US", description="Destination country code")
    description: str = Field(default="", description="Transaction memo or invoice description")
    risk_flags: List[str] = Field(default_factory=list, description="Pre-computed or detected risk indicators")


class Entity(BaseModel):
    id: str
    name: str
    entity_type: str = "INDIVIDUAL"  # INDIVIDUAL, CORPORATION, OFFSHORE_LLC, CRYPTO_EXCHANGE
    country: str = "US"
    risk_score: float = 0.0
    sanctions_status: bool = False
    pep_status: bool = False
    known_aliases: List[str] = Field(default_factory=list)


class AnomalyAlert(BaseModel):
    rule_id: str
    rule_name: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    entities_involved: List[str] = Field(default_factory=list)
    transactions_involved: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.85


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # account, entity, jurisdiction
    risk_level: str  # low, medium, high, critical
    country: str = "US"
    total_inflow: float = 0.0
    total_outflow: float = 0.0
    sanctioned: bool = False
    pep: bool = False


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str
    amount: float
    currency: str = "USD"
    count: int = 1
    transaction_ids: List[str] = Field(default_factory=list)
    is_flagged: bool = False


class GraphData(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)


class AgentThought(BaseModel):
    agent_name: str
    step: int
    action: str
    tool: Optional[str] = None
    tool_input: Optional[Any] = None
    tool_output: Optional[Any] = None
    thought: str
    observation: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SARDraft(BaseModel):
    sar_id: str
    filing_institution: str = "FinAudit Sentinel Bank, N.A."
    filing_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    primary_subject: str
    associated_entities: List[str] = Field(default_factory=list)
    total_suspicious_amount: float
    currency: str = "USD"
    typologies_identified: List[str] = Field(default_factory=list)
    suspicious_date_range: str
    jurisdictions_involved: List[str] = Field(default_factory=list)
    narrative_summary: str
    chronological_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    regulatory_violations: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    overall_risk_score: float  # 0 to 100
    confidence_score: float  # 0.0 to 1.0
    status: str = "DRAFT_PENDING_REVIEW"


class InvestigationRequest(BaseModel):
    scenario_id: Optional[str] = None
    transactions: Optional[List[Transaction]] = None
    focus_entity: Optional[str] = None
    provider: Optional[str] = "default"  # gemini, openai, local, mock


class InvestigationResult(BaseModel):
    investigation_id: str
    scenario_name: str
    total_transactions: int
    flagged_transactions_count: int
    high_risk_entities_count: int
    anomalies: List[AnomalyAlert]
    agent_trace: List[AgentThought]
    sar_draft: SARDraft
    graph_data: GraphData
    completed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
