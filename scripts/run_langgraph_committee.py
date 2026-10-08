"""LangGraph Multi-Agent Committee Demonstration Script.

Runs a live deliberation of the Investment Committee powered by LangGraph,
visualizing state transitions, multi-agent critiques, and consensus verdict.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.agents.langgraph_committee import run_langgraph_committee
from core.schemas import InvestorMandate, Opportunity, RiskTolerance, StrategyType


def main():
    print("=" * 80)
    print("  REAL ESTATE CAPITAL OS — LANGGRAPH INVESTMENT COMMITTEE ENGINE")
    print("=" * 80)

    # 1. Active Investor Mandate
    mandate = InvestorMandate(
        investor_name="Grupo Inversor Nueva Cordoba",
        capital_available=250000.0,
        currency="USD",
        target_irr=0.18,  # 18% hurdle
        investment_horizon_months=12,
        risk_tolerance=RiskTolerance.MEDIUM,
        geography=["Cordoba"],
        strategies=[StrategyType.RENOVATE_AND_SELL],
    )

    # 2. Candidate Opportunity in Córdoba
    opportunity = Opportunity(
        title="Piso Clasico en San Lorenzo (Nueva Cordoba)",
        location="Nueva Cordoba, Cordoba",
        strategy=StrategyType.RENOVATE_AND_SELL,
        asking_price=88000.0,
        projected_purchase_price=76000.0,
        estimated_capex=14000.0,
        holding_period_months=11,
        projected_exit_value=128000.0,
    )

    print("\n[INPUT DEAL CONTEXT]")
    print(f"Asset:               {opportunity.title}")
    print(f"Location / Strategy: {opportunity.location} | {opportunity.strategy.value}")
    print(f"Acquisition:         ${opportunity.projected_purchase_price:,.0f} (Asking: ${opportunity.asking_price:,.0f})")
    print(f"Capex:               ${opportunity.estimated_capex:,.0f} | Holding: {opportunity.holding_period_months} months")
    print(f"Exit Valuation:      ${opportunity.projected_exit_value:,.0f}")
    print(f"Investor Target:     {mandate.investor_name} | Target IRR: {mandate.target_irr:.1%}")

    print("\n" + "-" * 80)
    print("  EXECUTING LANGGRAPH STATEGRAPH DELIBERATION STREAM")
    print("-" * 80)

    # 3. Execute LangGraph StateGraph
    final_state = run_langgraph_committee(opportunity, mandate)

    # Trace agent nodes
    print("\n>>> NODE 1: [underwriter_node]")
    print(f"    {final_state['underwriter_critique']}")

    print("\n>>> NODE 2: [risk_officer_node]")
    print(f"    {final_state['risk_critique']}")

    print("\n>>> NODE 3: [coordinator_node]")
    print(f"    Verdict:           [{final_state['verdict'].upper()}]")
    print(f"    Rationale:         {final_state['rationale']}")
    if final_state["max_recommended_bid"]:
        print(f"    Recommended Bid:   ${final_state['max_recommended_bid']:,.0f} USD")

    print("\n--- GRAPH AUDIT TRAIL ---")
    for i, step in enumerate(final_state["audit_trail"], 1):
        print(f"  Step {i}: {step}")

    print("\n" + "=" * 80)
    print("  LANGGRAPH EXECUTION COMPLETED: STATEFUL MULTI-AGENT CONSENSUS REACHED")
    print("=" * 80)


if __name__ == "__main__":
    main()
