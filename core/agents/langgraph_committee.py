"""LangGraph Multi-Agent Investment Committee for Real Estate Capital OS.

Implements Sections 16 & 17 of Master Project Document using LangGraph (StateGraph):
- State-based multi-agent orchestration
- Distinct specialist nodes (Underwriter, Risk Officer, Coordinator)
- Natural language reasoning grounded in deterministic quantitative tools
- Tightly integrated with canonical Pydantic models
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph

from core.agents.coordinator import InvestmentCommitteeCoordinator
from core.memo import generate_investment_memo
from core.schemas import (
    InvestmentMemo,
    InvestorMandate,
    Opportunity,
    UnderwritingModel,
)
from core.underwriting import run_underwriting


class CommitteeState(TypedDict):
    """Shared state dictionary representing the deal context across graph nodes."""
    opportunity: Dict[str, Any]
    mandate: Dict[str, Any]
    discount_rate_annual: float
    underwriting_data: Optional[Dict[str, Any]]
    underwriter_critique: Optional[str]
    risk_score: Optional[float]
    risk_critique: Optional[str]
    verdict: Optional[str]
    rationale: Optional[str]
    max_recommended_bid: Optional[float]
    memo_markdown: Optional[str]
    audit_trail: List[str]


def underwriter_node(state: CommitteeState) -> Dict[str, Any]:
    """Node 1: Quantitative Underwriter. Runs financial tools and synthesizes economic rationale."""
    opp = Opportunity.model_validate(state["opportunity"])
    discount_rate = state.get("discount_rate_annual", 0.10)
    uw = run_underwriting(opp, discount_rate_annual=discount_rate)

    downside = uw.scenarios.get("Downside") or uw.scenarios.get("downside")
    downside_irr = downside.irr_annualized if downside else 0.0
    downside_profit = downside.net_profit if downside else 0.0

    critique = (
        f"[Analista Cuantitativo]: Oportunidad '{opp.title}' en {opp.location}. "
        f"Inversión inicial requerida: ${opp.total_capital_required:,.0f} USD. "
        f"Proyección Base: TIR {uw.irr_annualized:.1%}, MOIC {uw.moic:.2f}x, VAN ${uw.npv:,.0f} USD. "
        f"Escenario Adverso: Utilidad ${downside_profit:,.0f} USD (TIR {downside_irr:.1%})."
    )

    trail = list(state.get("audit_trail", []))
    trail.append("Underwriter evaluated cashflows and scenarios.")

    return {
        "underwriting_data": uw.model_dump(),
        "underwriter_critique": critique,
        "audit_trail": trail,
    }


def risk_node(state: CommitteeState) -> Dict[str, Any]:
    """Node 2: Independent Risk Officer. Stress-tests execution, duration, and downside downside."""
    opp = Opportunity.model_validate(state["opportunity"])
    mandate = InvestorMandate.model_validate(state["mandate"])
    uw_data = state["underwriting_data"]

    scenarios = uw_data.get("scenarios", {})
    downside_dict = scenarios.get("Downside") or scenarios.get("downside") or {}
    downside_profit = downside_dict.get("net_profit", 0.0)
    downside_irr = downside_dict.get("irr_annualized", 0.0)
    capex_ratio = opp.estimated_capex / opp.projected_purchase_price if opp.projected_purchase_price > 0 else 0

    flags = []
    score = 100.0

    if downside_profit < 0:
        flags.append("Pérdida de capital en Downside")
        score -= 35.0
    if capex_ratio > 0.30:
        flags.append(f"Alta intensidad de reforma ({capex_ratio:.1%})")
        score -= 20.0
    if opp.holding_period_months > 18:
        flags.append(f"Plazo prolongado ({opp.holding_period_months} meses)")
        score -= 15.0

    score = max(0.0, min(100.0, score))

    critique = (
        f"[Oficial de Riesgo]: Score asignado: {score:.0f}/100. "
        f"Alertas de riesgo: {', '.join(flags) if flags else 'Dentro de parámetros normales'}. "
        f"TIR en estrés: {downside_irr:.1%}. "
        f"Intensidad de obra: {capex_ratio:.1%} sobre precio de adquisición."
    )

    trail = list(state.get("audit_trail", []))
    trail.append("Risk Officer stress-tested execution and downside.")

    return {
        "risk_score": score,
        "risk_critique": critique,
        "audit_trail": trail,
    }


def coordinator_node(state: CommitteeState) -> Dict[str, Any]:
    """Node 3: Committee Coordinator. Reaches consensus verdict and drafts the Investment Memo."""
    opp = Opportunity.model_validate(state["opportunity"])
    mandate = InvestorMandate.model_validate(state["mandate"])
    coordinator = InvestmentCommitteeCoordinator()

    # Leverage the consensus solver
    verdict_obj = coordinator.evaluate_deal(
        opportunity=opp,
        mandate=mandate,
        discount_rate_annual=state.get("discount_rate_annual", 0.10),
    )

    memo_md = verdict_obj.memo.markdown_content if verdict_obj.memo else None

    trail = list(state.get("audit_trail", []))
    trail.append(f"Coordinator issued consensus verdict: {verdict_obj.verdict.value.upper()}.")

    return {
        "verdict": verdict_obj.verdict.value,
        "rationale": verdict_obj.rationale,
        "max_recommended_bid": verdict_obj.max_recommended_bid,
        "memo_markdown": memo_md,
        "audit_trail": trail,
    }


def build_committee_graph() -> StateGraph:
    """Build and compile the LangGraph StateGraph for the Investment Committee."""
    builder = StateGraph(CommitteeState)

    builder.add_node("underwriter", underwriter_node)
    builder.add_node("risk_officer", risk_node)
    builder.add_node("coordinator", coordinator_node)

    builder.add_edge(START, "underwriter")
    builder.add_edge("underwriter", "risk_officer")
    builder.add_edge("risk_officer", "coordinator")
    builder.add_edge("coordinator", END)

    return builder.compile()


# Compiled singleton graph
committee_graph = build_committee_graph()


def run_langgraph_committee(
    opportunity: Opportunity,
    mandate: InvestorMandate,
    discount_rate_annual: float = 0.10,
) -> CommitteeState:
    """Execute the multi-agent committee graph on a given opportunity and mandate."""
    initial_state: CommitteeState = {
        "opportunity": opportunity.model_dump(),
        "mandate": mandate.model_dump(),
        "discount_rate_annual": discount_rate_annual,
        "underwriting_data": None,
        "underwriter_critique": None,
        "risk_score": None,
        "risk_critique": None,
        "verdict": None,
        "rationale": None,
        "max_recommended_bid": None,
        "memo_markdown": None,
        "audit_trail": [],
    }

    final_state = committee_graph.invoke(initial_state)
    return final_state
