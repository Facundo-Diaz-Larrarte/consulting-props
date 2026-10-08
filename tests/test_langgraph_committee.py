"""Tests for LangGraph Multi-Agent Investment Committee."""

import pytest
from core.agents.langgraph_committee import committee_graph, run_langgraph_committee
from core.schemas import InvestorMandate, Opportunity, RiskTolerance, StrategyType


@pytest.fixture
def mandate() -> InvestorMandate:
    return InvestorMandate(
        investor_name="Inversor Alfa LangGraph",
        capital_available=200000.0,
        currency="USD",
        target_irr=0.16,
        investment_horizon_months=12,
        risk_tolerance=RiskTolerance.MEDIUM,
        geography=["Cordoba"],
        strategies=[StrategyType.RENOVATE_AND_SELL],
    )


@pytest.fixture
def strong_opp() -> Opportunity:
    return Opportunity(
        title="Oportunidad Nva Cba LangGraph",
        location="Nueva Cordoba, Cordoba",
        strategy=StrategyType.RENOVATE_AND_SELL,
        asking_price=80000.0,
        projected_purchase_price=70000.0,
        estimated_capex=12000.0,
        holding_period_months=10,
        projected_exit_value=120000.0,
    )


def test_langgraph_compilation():
    assert committee_graph is not None
    assert "underwriter" in committee_graph.nodes
    assert "risk_officer" in committee_graph.nodes
    assert "coordinator" in committee_graph.nodes


def test_langgraph_execution_approved(mandate, strong_opp):
    final_state = run_langgraph_committee(strong_opp, mandate)

    assert final_state["verdict"] == "approved"
    assert "Analista Cuantitativo" in final_state["underwriter_critique"]
    assert "Oficial de Riesgo" in final_state["risk_critique"]
    assert final_state["risk_score"] is not None
    assert final_state["memo_markdown"] is not None
    assert len(final_state["audit_trail"]) == 3


def test_langgraph_execution_counter_offer(mandate):
    overpriced_opp = Opportunity(
        title="Oportunidad Cara LangGraph",
        location="Nueva Cordoba, Cordoba",
        strategy=StrategyType.RENOVATE_AND_SELL,
        asking_price=95000.0,
        projected_purchase_price=90000.0,
        estimated_capex=15000.0,
        holding_period_months=12,
        projected_exit_value=120000.0,
    )
    final_state = run_langgraph_committee(overpriced_opp, mandate)

    assert final_state["verdict"] == "counter_offer"
    assert final_state["max_recommended_bid"] is not None
    assert final_state["max_recommended_bid"] < overpriced_opp.projected_purchase_price
    assert "Contraoferta" in final_state["rationale"]
