"""Domain schemas for Real Estate Capital OS.

Implements the 5 canonical objects defined in Master Project Document Section 43:
1. Investor Mandate
2. Opportunity
3. Underwriting Model
4. Investment Memo
5. Deal Pipeline
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class StrategyType(str, Enum):
    """Investment strategies defined in Section 10."""
    BUY_AND_HOLD = "buy_and_hold"
    RENOVATE_AND_SELL = "renovate_and_sell"
    REPOSITION_AND_SELL = "reposition_and_sell"
    SPLIT_AND_SELL = "split_and_sell"
    CHANGE_OF_USE = "change_of_use"
    PRE_CONSTRUCTION = "pre_construction"
    DEVELOPMENT = "development"
    DISTRESSED = "distressed"
    CONSTRUCTION_FINANCING = "construction_financing"
    DEVELOPER_CAPITAL = "developer_capital"


class RiskTolerance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DealStage(str, Enum):
    """Deal pipeline lifecycle stages defined in Section 9 and 20."""
    RAW = "raw"
    NORMALIZED = "normalized"
    CONTACTED = "contacted"
    VERIFIED = "verified"
    UNDERWRITTEN = "underwritten"
    APPROVED = "approved"
    PRESENTED = "presented"
    NEGOTIATION = "negotiation"
    DEAL = "deal"
    CLOSED = "closed"
    EXIT = "exit"


# Object 1: Investor Mandate
class InvestorMandate(BaseModel):
    """Structured investment profile of an investor (Section 7)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    investor_name: str
    capital_available: float = Field(..., gt=0, description="Total capital available in USD")
    currency: str = "USD"
    target_irr: float = Field(..., gt=0, lt=2.0, description="Annual target IRR (e.g. 0.15 for 15%)")
    investment_horizon_months: int = Field(..., gt=0, description="Target timeframe in months")
    risk_tolerance: RiskTolerance = RiskTolerance.MEDIUM
    minimum_liquidity: float = Field(default=0.15, ge=0.0, le=1.0)
    geography: List[str] = Field(default_factory=lambda: ["Cordoba"])
    strategies: List[StrategyType] = Field(default_factory=lambda: [StrategyType.RENOVATE_AND_SELL])
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("geography", mode="after")
    @classmethod
    def validate_geography(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one target geography must be specified")
        return v


# Object 2: Opportunity
class Opportunity(BaseModel):
    """Real estate asset transformed into an investment opportunity (Section 9, 10)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    location: str
    strategy: StrategyType = StrategyType.RENOVATE_AND_SELL
    asking_price: float = Field(..., gt=0)
    projected_purchase_price: float = Field(..., gt=0)
    estimated_capex: float = Field(default=0.0, ge=0)
    closing_costs_pct: float = Field(default=0.06, ge=0, le=0.25, description="Notary, legal, stamps, commissions (e.g. 0.06 = 6%)")
    holding_period_months: int = Field(..., gt=0, description="Total estimated duration in months")
    projected_exit_value: float = Field(..., gt=0)
    monthly_gross_rent: float = Field(default=0.0, ge=0)
    monthly_operating_expenses: float = Field(default=0.0, ge=0)
    status: DealStage = DealStage.RAW
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_initial_cost(self) -> float:
        """Purchase price + transaction closing costs."""
        return self.projected_purchase_price * (1.0 + self.closing_costs_pct)

    @property
    def total_capital_required(self) -> float:
        """Total capital deployment: Initial cost + Capex."""
        return self.total_initial_cost + self.estimated_capex


# Object 3: Underwriting Model
class ScenarioMetrics(BaseModel):
    """Results for a single economic scenario (Downside, Base, Upside)."""
    scenario_name: str
    exit_value: float
    total_capital_invested: float
    net_profit: float
    irr_annualized: float
    npv: float
    moic: float
    roi: float


class SensitivityPoint(BaseModel):
    """Sensitivity analysis point (e.g. price change vs IRR)."""
    purchase_price: float
    exit_value: float
    capex: float
    holding_period_months: int
    irr_annualized: float
    moic: float
    npv: float


class UnderwritingModel(BaseModel):
    """Deterministic financial underwriting output (Section 11, 12, 13)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    opportunity_id: str
    discount_rate_annual: float = 0.10
    total_capital_deployed: float
    net_profit: float
    irr_annualized: float
    npv: float
    moic: float
    roi: float
    monthly_cashflows: List[float]
    scenarios: Dict[str, ScenarioMetrics]
    sensitivities: List[SensitivityPoint] = Field(default_factory=list)
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Object 4: Investment Memo
class InvestmentMemo(BaseModel):
    """Standardized institutional deal summary (Section 15)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    opportunity_id: str
    title: str
    target_geography: str
    strategy: StrategyType
    capital_required: float
    projected_holding_months: int
    target_irr: float
    target_moic: float
    npv: float
    thesis: str
    scenarios_summary: str
    key_risks: List[str]
    exit_strategy: str
    markdown_content: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Object 5: Deal Pipeline
class PipelineEvent(BaseModel):
    from_stage: DealStage
    to_stage: DealStage
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: Optional[str] = None


class DealPipelineItem(BaseModel):
    """Tracking entity for an opportunity progressing through deal stages (Section 20)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    opportunity_id: str
    mandate_id: Optional[str] = None
    current_stage: DealStage = DealStage.RAW
    history: List[PipelineEvent] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def transition_to(self, new_stage: DealStage, reason: Optional[str] = None) -> None:
        """Record stage transition in history."""
        event = PipelineEvent(
            from_stage=self.current_stage,
            to_stage=new_stage,
            reason=reason
        )
        self.history.append(event)
        self.current_stage = new_stage
        self.updated_at = datetime.now(timezone.utc)
