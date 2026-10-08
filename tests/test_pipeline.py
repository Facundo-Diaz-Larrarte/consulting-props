import sys
from pathlib import Path

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from core.schemas import (
    DealPipelineItem,
    DealStage,
    InvestorMandate,
    Opportunity,
    RiskTolerance,
    StrategyType,
)
from core.pipeline import (
    DealPipelineEngine,
    DealPipelineOrchestrator,
    InvalidTransitionError,
)
from core.agents.coordinator import CommitteeVerdict, CommitteeVerdictType
from core.tools.idecor import audit_property_valuation
from core.underwriting import run_underwriting


@pytest.fixture
def sample_opportunity() -> Opportunity:
    return Opportunity(
        title="2D Nueva Córdoba Oportunidad",
        location="Nueva Córdoba, Córdoba",
        strategy=StrategyType.RENOVATE_AND_SELL,
        asking_price=90000.0,
        projected_purchase_price=80000.0,
        estimated_capex=15000.0,
        holding_period_months=8,
        projected_exit_value=130000.0,
        usable_area_m2=70.0,
    )


@pytest.fixture
def sample_mandate() -> InvestorMandate:
    return InvestorMandate(
        investor_name="Family Office Córdoba",
        capital_available=150000.0,
        target_irr=0.15,
        investment_horizon_months=12,
        geography=["Cordoba"],
        strategies=[StrategyType.RENOVATE_AND_SELL],
        risk_tolerance=RiskTolerance.MEDIUM,
    )


class TestPipelineTransitions:
    """Verify transition validation and institutional gate enforcement."""

    def test_illegal_jump_raises_error(self, sample_opportunity: Opportunity):
        engine = DealPipelineEngine()
        item = DealPipelineItem(opportunity_id=sample_opportunity.id, current_stage=DealStage.RAW)

        with pytest.raises(InvalidTransitionError, match="Transición inválida"):
            engine.transition(item, DealStage.APPROVED)

    def test_terminal_state_cannot_transition(self, sample_opportunity: Opportunity):
        engine = DealPipelineEngine()
        item = DealPipelineItem(opportunity_id=sample_opportunity.id, current_stage=DealStage.REJECTED)

        with pytest.raises(InvalidTransitionError, match="Transición inválida"):
            engine.transition(item, DealStage.NORMALIZED)

    def test_gate_verification_requires_market_audit(self, sample_opportunity: Opportunity):
        engine = DealPipelineEngine()
        item = DealPipelineItem(opportunity_id=sample_opportunity.id, current_stage=DealStage.NORMALIZED)

        with pytest.raises(InvalidTransitionError, match="Gate fallido: No se puede verificar"):
            engine.transition(item, DealStage.VERIFIED, market_audit=None)

    def test_gate_underwritten_requires_model(self, sample_opportunity: Opportunity):
        engine = DealPipelineEngine()
        item = DealPipelineItem(opportunity_id=sample_opportunity.id, current_stage=DealStage.VERIFIED)

        with pytest.raises(InvalidTransitionError, match="Gate fallido: No se puede marcar como underwritten"):
            engine.transition(item, DealStage.UNDERWRITTEN, underwriting=None)

    def test_gate_approved_requires_committee_verdict(self, sample_opportunity: Opportunity):
        engine = DealPipelineEngine()
        item = DealPipelineItem(opportunity_id=sample_opportunity.id, current_stage=DealStage.UNDERWRITTEN)

        with pytest.raises(InvalidTransitionError, match="Gate fallido: No se puede aprobar"):
            engine.transition(item, DealStage.APPROVED, committee_verdict=None)


class TestPipelineOrchestrator:
    """Verify automated end-to-end deal execution through Section 20 lifecycle."""

    def test_full_cycle_approved_deal(self, sample_opportunity: Opportunity, sample_mandate: InvestorMandate):
        orchestrator = DealPipelineOrchestrator()
        result = orchestrator.run_full_cycle(sample_opportunity, sample_mandate)

        # Final stage should be PRESENTED
        assert result.pipeline_item.current_stage == DealStage.PRESENTED
        assert result.opportunity.status == DealStage.PRESENTED
        assert result.memo is not None
        assert result.underwriting is not None
        assert result.market_audit is not None
        assert result.committee_verdict.verdict == CommitteeVerdictType.APPROVED

        # Verify audit trail history has all sequential stages
        stages = [e.to_stage for e in result.pipeline_item.history]
        assert stages == [
            DealStage.NORMALIZED,
            DealStage.VERIFIED,
            DealStage.UNDERWRITTEN,
            DealStage.APPROVED,
            DealStage.PRESENTED,
        ]

        # Verify actors in audit trail
        actors = [e.actor for e in result.pipeline_item.history]
        assert "IngestionAgent" in actors
        assert "MarketDataAgent" in actors
        assert "UnderwritingAgent" in actors
        assert "InvestmentCommittee" in actors
        assert "CoordinatorAgent" in actors

    def test_full_cycle_counter_offer_deal(self, sample_mandate: InvestorMandate):
        # Deal is overpriced: good asset but needs negotiation
        overpriced_opp = Opportunity(
            title="Piso Caro General Paz",
            location="General Paz, Córdoba",
            strategy=StrategyType.RENOVATE_AND_SELL,
            asking_price=110000.0,
            projected_purchase_price=100000.0,
            estimated_capex=15000.0,
            holding_period_months=12,
            projected_exit_value=135000.0,
            usable_area_m2=75.0,
        )

        orchestrator = DealPipelineOrchestrator()
        result = orchestrator.run_full_cycle(overpriced_opp, sample_mandate)

        assert result.pipeline_item.current_stage == DealStage.NEGOTIATION
        assert result.committee_verdict.verdict == CommitteeVerdictType.COUNTER_OFFER
        assert "max_recommended_bid" in result.pipeline_item.history[-1].metadata

    def test_full_cycle_rejected_mismatch_deal(self, sample_mandate: InvestorMandate):
        # Mismatch in strategy (Commercial development vs Residential flip)
        mismatch_opp = Opportunity(
            title="Lote Comercial Suburbano",
            location="Córdoba",
            strategy=StrategyType.DEVELOPMENT,  # Not in mandate strategies
            asking_price=200000.0,
            projected_purchase_price=180000.0,
            holding_period_months=24,
            projected_exit_value=250000.0,
        )

        orchestrator = DealPipelineOrchestrator()
        result = orchestrator.run_full_cycle(mismatch_opp, sample_mandate)

        assert result.pipeline_item.current_stage == DealStage.REJECTED
        assert result.committee_verdict.verdict == CommitteeVerdictType.REJECTED

    def test_full_cycle_from_raw_dict(self, sample_mandate: InvestorMandate):
        # Ingestion from unstructured/raw broker dictionary
        raw_dict = {
            "title": "Departamento en Guemes reciclado",
            "location": "Guemes, Cordoba",
            "strategy": "renovate_and_sell",
            "price": 75000.0,
            "capex": 10000.0,
            "exit_value": 115000.0,
            "duration": 6,
            "usable_area_m2": 75.0,
        }

        orchestrator = DealPipelineOrchestrator()
        result = orchestrator.run_full_cycle(raw_dict, sample_mandate)

        assert result.opportunity.projected_purchase_price == 75000.0
        assert result.pipeline_item.current_stage == DealStage.PRESENTED
        assert result.memo is not None
