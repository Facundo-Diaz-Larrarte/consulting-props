"""Deal Pipeline Engine for Real Estate Capital OS.

Implements Sections 20 (*Flujo completo de un deal*) and 43 (*Object 5 — Deal Pipeline*):
- Strict state-machine transitions and institutional gates
- Transition audit trail logging with actors and metadata
- End-to-end automated deal execution from Sourcing to Presented / Negotiation
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field

from core.agents.coordinator import CommitteeVerdict, CommitteeVerdictType, InvestmentCommitteeCoordinator
from core.agents.ingestion import IngestionAgent, normalize_opportunity
from core.memo import generate_investment_memo
from core.schemas import (
    DealPipelineItem,
    DealStage,
    InvestmentMemo,
    InvestorMandate,
    Opportunity,
    UnderwritingModel,
)
from core.tools.idecor import MarketValuationAudit, audit_property_valuation
from core.underwriting import run_underwriting


class InvalidTransitionError(Exception):
    """Raised when an illegal deal pipeline transition is attempted or gates are violated."""
    pass


# Strict allowable transitions between deal lifecycle stages
ALLOWED_TRANSITIONS: Dict[DealStage, Set[DealStage]] = {
    DealStage.RAW: {DealStage.NORMALIZED, DealStage.REJECTED},
    DealStage.NORMALIZED: {DealStage.CONTACTED, DealStage.VERIFIED, DealStage.REJECTED},
    DealStage.CONTACTED: {DealStage.VERIFIED, DealStage.REJECTED},
    DealStage.VERIFIED: {DealStage.UNDERWRITTEN, DealStage.REJECTED},
    DealStage.UNDERWRITTEN: {DealStage.APPROVED, DealStage.NEGOTIATION, DealStage.REJECTED},
    DealStage.APPROVED: {DealStage.PRESENTED, DealStage.NEGOTIATION, DealStage.REJECTED},
    DealStage.PRESENTED: {DealStage.NEGOTIATION, DealStage.DEAL, DealStage.REJECTED},
    DealStage.NEGOTIATION: {DealStage.DEAL, DealStage.REJECTED},
    DealStage.DEAL: {DealStage.CLOSED, DealStage.REJECTED},
    DealStage.CLOSED: {DealStage.EXIT},
    DealStage.EXIT: set(),  # Terminal state
    DealStage.REJECTED: set(),  # Terminal state
}


class DealPipelineEngine:
    """State machine engine enforcing institutional governance and lifecycle transitions."""

    @staticmethod
    def validate_transition(
        item: DealPipelineItem,
        target_stage: DealStage,
        opportunity: Optional[Opportunity] = None,
        underwriting: Optional[UnderwritingModel] = None,
        market_audit: Optional[MarketValuationAudit] = None,
        committee_verdict: Optional[CommitteeVerdict] = None,
        mandate: Optional[InvestorMandate] = None,
    ) -> None:
        """Validate if a state transition is permitted and institutional gates are satisfied."""
        current = item.current_stage

        # Check allowed transition graph
        allowed = ALLOWED_TRANSITIONS.get(current, set())
        if target_stage not in allowed:
            raise InvalidTransitionError(
                f"Transición inválida: No se puede mover el deal de '{current.value}' a '{target_stage.value}'."
            )

        # Gate 1: VERIFIED requires a completed market valuation audit
        if target_stage == DealStage.VERIFIED:
            if market_audit is None:
                raise InvalidTransitionError(
                    "Gate fallido: No se puede verificar el deal sin una auditoría de valuación zonal (IDECOR)."
                )

        # Gate 2: UNDERWRITTEN requires deterministic underwriting output
        if target_stage == DealStage.UNDERWRITTEN:
            if underwriting is None:
                raise InvalidTransitionError(
                    "Gate fallido: No se puede marcar como underwritten sin un modelo financiero calculado."
                )

        # Gate 3: APPROVED requires formal Investment Committee approval
        if target_stage == DealStage.APPROVED:
            if not committee_verdict or committee_verdict.verdict != CommitteeVerdictType.APPROVED:
                raise InvalidTransitionError(
                    "Gate fallido: No se puede aprobar el deal sin veredicto vinculante APPROVED del Comité de Inversión."
                )

        # Gate 4: PRESENTED requires an associated Investor Mandate
        if target_stage == DealStage.PRESENTED:
            if not item.mandate_id and not mandate:
                raise InvalidTransitionError(
                    "Gate fallido: No se puede presentar la oportunidad sin asociar un mandato de inversor calificado."
                )

    def transition(
        self,
        item: DealPipelineItem,
        target_stage: DealStage,
        reason: Optional[str] = None,
        actor: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
        opportunity: Optional[Opportunity] = None,
        underwriting: Optional[UnderwritingModel] = None,
        market_audit: Optional[MarketValuationAudit] = None,
        committee_verdict: Optional[CommitteeVerdict] = None,
        mandate: Optional[InvestorMandate] = None,
    ) -> DealPipelineItem:
        """Execute a validated stage transition and append the audit event."""
        self.validate_transition(
            item=item,
            target_stage=target_stage,
            opportunity=opportunity,
            underwriting=underwriting,
            market_audit=market_audit,
            committee_verdict=committee_verdict,
            mandate=mandate,
        )

        if mandate and not item.mandate_id:
            item.mandate_id = mandate.id

        if opportunity:
            opportunity.status = target_stage

        item.transition_to(
            new_stage=target_stage,
            reason=reason,
            actor=actor,
            metadata=metadata,
        )
        return item


class PipelineExecutionResult(BaseModel):
    """Encapsulates the complete state and artifacts produced during a pipeline lifecycle run."""
    pipeline_item: DealPipelineItem
    opportunity: Opportunity
    underwriting: Optional[UnderwritingModel] = None
    market_audit: Optional[MarketValuationAudit] = None
    committee_verdict: Optional[CommitteeVerdict] = None
    memo: Optional[InvestmentMemo] = None
    mandate: Optional[InvestorMandate] = None


class DealPipelineOrchestrator:
    """Orchestrates an opportunity from raw sourcing to final committee presentation."""

    def __init__(self):
        self.engine = DealPipelineEngine()
        self.ingestion = IngestionAgent()
        self.coordinator = InvestmentCommitteeCoordinator()

    def run_full_cycle(
        self,
        raw_opportunity: Union[Dict[str, Any], Opportunity],
        mandate: InvestorMandate,
        discount_rate_annual: float = 0.10,
    ) -> PipelineExecutionResult:
        """Advance an opportunity through the automated pipeline stages of Section 20."""
        # 1. Initialize Pipeline Item (RAW)
        if isinstance(raw_opportunity, Opportunity):
            opp = raw_opportunity
        else:
            opp = normalize_opportunity(raw_opportunity)

        pipeline_item = DealPipelineItem(
            opportunity_id=opp.id,
            mandate_id=mandate.id,
            current_stage=DealStage.RAW,
        )

        # 2. Stage RAW -> NORMALIZED
        self.engine.transition(
            item=pipeline_item,
            target_stage=DealStage.NORMALIZED,
            reason="Oportunidad normalizada e ingresada al Opportunity Book.",
            actor="IngestionAgent",
            opportunity=opp,
        )

        # 3. Stage NORMALIZED -> VERIFIED (IDECOR Valuation)
        market_audit = audit_property_valuation(opp)
        self.engine.transition(
            item=pipeline_item,
            target_stage=DealStage.VERIFIED,
            reason=f"Valuación zonal auditada contra IDECOR/OMI ({market_audit.neighborhood}).",
            actor="MarketDataAgent",
            opportunity=opp,
            market_audit=market_audit,
            metadata=market_audit.model_dump(),
        )

        # 4. Stage VERIFIED -> UNDERWRITTEN (Financial Engine)
        underwriting = run_underwriting(opp, discount_rate_annual=discount_rate_annual)
        self.engine.transition(
            item=pipeline_item,
            target_stage=DealStage.UNDERWRITTEN,
            reason="Modelo financiero determinístico calculado (TIR base, VAN, MOIC, Downside).",
            actor="UnderwritingAgent",
            opportunity=opp,
            underwriting=underwriting,
            metadata={
                "irr_annualized": underwriting.irr_annualized,
                "moic": underwriting.moic,
                "npv": underwriting.npv,
            },
        )

        # 5. Stage UNDERWRITTEN -> Investment Committee Decision
        verdict = self.coordinator.evaluate_deal(
            opportunity=opp,
            mandate=mandate,
            discount_rate_annual=discount_rate_annual,
        )

        memo: Optional[InvestmentMemo] = None

        if verdict.verdict == CommitteeVerdictType.APPROVED:
            # Transition to APPROVED
            self.engine.transition(
                item=pipeline_item,
                target_stage=DealStage.APPROVED,
                reason=verdict.rationale,
                actor="InvestmentCommittee",
                opportunity=opp,
                underwriting=underwriting,
                market_audit=market_audit,
                committee_verdict=verdict,
                mandate=mandate,
            )
            # Generate Memo & Transition to PRESENTED
            memo = verdict.memo or generate_investment_memo(
                opportunity=opp,
                underwriting=underwriting,
                thesis=f"Oportunidad calificada en {opp.location} aprobada por el comité.",
            )
            self.engine.transition(
                item=pipeline_item,
                target_stage=DealStage.PRESENTED,
                reason=f"Memo institucional generado para el mandato de {mandate.investor_name}.",
                actor="CoordinatorAgent",
                opportunity=opp,
                mandate=mandate,
                metadata={"memo_id": memo.id},
            )

        elif verdict.verdict == CommitteeVerdictType.COUNTER_OFFER:
            # Deal has good asset fundamentals but needs price negotiation
            self.engine.transition(
                item=pipeline_item,
                target_stage=DealStage.NEGOTIATION,
                reason=verdict.rationale,
                actor="InvestmentCommittee",
                opportunity=opp,
                underwriting=underwriting,
                market_audit=market_audit,
                committee_verdict=verdict,
                mandate=mandate,
                metadata={"max_recommended_bid": verdict.max_recommended_bid},
            )
            memo = verdict.memo

        else:
            # Fatal mismatch or unviable economics -> REJECTED
            self.engine.transition(
                item=pipeline_item,
                target_stage=DealStage.REJECTED,
                reason=verdict.rationale,
                actor="InvestmentCommittee",
                opportunity=opp,
                underwriting=underwriting,
                market_audit=market_audit,
                committee_verdict=verdict,
                mandate=mandate,
            )

        return PipelineExecutionResult(
            pipeline_item=pipeline_item,
            opportunity=opp,
            underwriting=underwriting,
            market_audit=market_audit,
            committee_verdict=verdict,
            memo=memo,
            mandate=mandate,
        )
