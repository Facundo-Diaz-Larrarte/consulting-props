"""Tests for Investment Committee and Multi-Agent Consensus."""

import pytest
from core.agents.committee import MatchingAgent, RiskAgent, UnderwritingAgent
from core.agents.coordinator import CommitteeVerdictType, InvestmentCommitteeCoordinator
from core.schemas import InvestorMandate, Opportunity, RiskTolerance, StrategyType


@pytest.fixture
def cordoba_mandate() -> InvestorMandate:
    return InvestorMandate(
        investor_name="Inversiones del Centro",
        capital_available=250000.0,
        currency="USD",
        target_irr=0.18,  # 18% target
        investment_horizon_months=18,
        risk_tolerance=RiskTolerance.MEDIUM,
        geography=["Cordoba"],
        strategies=[StrategyType.RENOVATE_AND_SELL],
    )


@pytest.fixture
def profitable_opportunity() -> Opportunity:
    return Opportunity(
        title="Piso en Nueva Cordoba",
        location="Nueva Cordoba, Cordoba",
        strategy=StrategyType.RENOVATE_AND_SELL,
        asking_price=90000.0,
        projected_purchase_price=78000.0,
        estimated_capex=15000.0,
        holding_period_months=12,
        projected_exit_value=135000.0,
    )


def test_committee_approves_strong_deal(cordoba_mandate, profitable_opportunity):
    coordinator = InvestmentCommitteeCoordinator()
    verdict = coordinator.evaluate_deal(profitable_opportunity, cordoba_mandate)

    assert verdict.verdict == CommitteeVerdictType.APPROVED
    assert verdict.underwriting.irr_annualized >= cordoba_mandate.target_irr
    assert verdict.risk.is_acceptable_risk is True
    assert verdict.match.is_hard_match is True
    assert verdict.memo is not None
    assert "Aprobado por el Comité" in verdict.rationale


def test_committee_rejects_structural_mismatch(cordoba_mandate):
    # Strategy mismatch (Development instead of Renovate)
    dev_opp = Opportunity(
        title="Lote en las Sierras",
        location="Villa Carlos Paz, Cordoba",
        strategy=StrategyType.DEVELOPMENT,
        asking_price=100000.0,
        projected_purchase_price=90000.0,
        estimated_capex=40000.0,
        holding_period_months=24,
        projected_exit_value=180000.0,
    )
    coordinator = InvestmentCommitteeCoordinator()
    verdict = coordinator.evaluate_deal(dev_opp, cordoba_mandate)

    assert verdict.verdict == CommitteeVerdictType.REJECTED
    assert verdict.match.strategy_fit is False
    assert "incompatibilidad estructural" in verdict.rationale


def test_committee_counter_offers_overpriced_deal(cordoba_mandate):
    # Deal has good location/strategy, but asking price is too high to reach 18% IRR
    overpriced_opp = Opportunity(
        title="Depto General Paz Caro",
        location="General Paz, Cordoba",
        strategy=StrategyType.RENOVATE_AND_SELL,
        asking_price=110000.0,
        projected_purchase_price=105000.0,
        estimated_capex=15000.0,
        holding_period_months=12,
        projected_exit_value=135000.0,
    )
    coordinator = InvestmentCommitteeCoordinator()
    verdict = coordinator.evaluate_deal(overpriced_opp, cordoba_mandate)

    assert verdict.verdict == CommitteeVerdictType.COUNTER_OFFER
    assert verdict.max_recommended_bid is not None
    assert verdict.max_recommended_bid < overpriced_opp.projected_purchase_price
    assert "Contraoferta recomendada" in verdict.rationale
    assert verdict.memo is not None


def test_counter_offer_reaches_target_irr(cordoba_mandate):
    coordinator = InvestmentCommitteeCoordinator()
    overpriced_opp = Opportunity(
        title="Depto Guemes Overpriced",
        location="Guemes, Cordoba",
        strategy=StrategyType.RENOVATE_AND_SELL,
        asking_price=100000.0,
        projected_purchase_price=95000.0,
        estimated_capex=15000.0,
        holding_period_months=12,
        projected_exit_value=130000.0,
    )
    verdict = coordinator.evaluate_deal(overpriced_opp, cordoba_mandate)
    assert verdict.verdict == CommitteeVerdictType.COUNTER_OFFER

    # Test the counter-offer purchase price achieves target IRR
    bid_opp = overpriced_opp.model_copy(update={"projected_purchase_price": verdict.max_recommended_bid})
    bid_uw = coordinator.underwriter.evaluate(bid_opp)
    assert bid_uw.irr_annualized >= (cordoba_mandate.target_irr - 0.01)  # within 1% rounding
