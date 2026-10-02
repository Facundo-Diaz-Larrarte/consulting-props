"""Investment Committee Simulation: Multi-Deal Capital Allocation Session.

Simulates a real-world session of the Investment Committee where multiple
competing opportunities in Córdoba are evaluated against an active Investor Mandate.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.agents.coordinator import CommitteeVerdictType, InvestmentCommitteeCoordinator
from core.schemas import (
    DealStage,
    InvestorMandate,
    Opportunity,
    RiskTolerance,
    StrategyType,
)


def run_committee_simulation():
    print("=" * 80)
    print("  REAL ESTATE CAPITAL OS — INVESTMENT COMMITTEE SESSION (CORDOBA)")
    print("=" * 80)

    # 1. Active Investor Mandate
    mandate = InvestorMandate(
        investor_name="Fondo Privado Cordoba Capital",
        capital_available=350000.0,
        currency="USD",
        target_irr=0.17,  # 17% hurdle
        investment_horizon_months=18,
        risk_tolerance=RiskTolerance.MEDIUM,
        geography=["Cordoba"],
        strategies=[StrategyType.RENOVATE_AND_SELL],
    )

    print("\n--- ACTIVE MANDATE ---")
    print(f"Investor:           {mandate.investor_name}")
    print(f"Available Capital:  ${mandate.capital_available:,.0f} USD")
    print(f"Hurdle Rate (IRR):  {mandate.target_irr:.1%} annual")
    print(f"Strategy / Market:  {', '.join(s.value for s in mandate.strategies)} in {', '.join(mandate.geography)}")

    # 2. Competing Opportunities
    deals = [
        Opportunity(
            title="Depto Obispo Oro (Nueva Cordoba)",
            location="Nueva Cordoba, Cordoba",
            strategy=StrategyType.RENOVATE_AND_SELL,
            asking_price=85000.0,
            projected_purchase_price=74000.0,
            estimated_capex=14000.0,
            holding_period_months=10,
            projected_exit_value=125000.0,
            status=DealStage.NORMALIZED,
        ),
        Opportunity(
            title="Piso 24 de Septiembre (General Paz)",
            location="General Paz, Cordoba",
            strategy=StrategyType.RENOVATE_AND_SELL,
            asking_price=105000.0,
            projected_purchase_price=98000.0,
            estimated_capex=15000.0,
            holding_period_months=12,
            projected_exit_value=130000.0,
            status=DealStage.NORMALIZED,
        ),
        Opportunity(
            title="Casona Tejeda (Cerro de las Rosas)",
            location="Cerro de las Rosas, Cordoba",
            strategy=StrategyType.RENOVATE_AND_SELL,
            asking_price=280000.0,
            projected_purchase_price=260000.0,
            estimated_capex=90000.0,
            holding_period_months=26,
            projected_exit_value=430000.0,
            status=DealStage.NORMALIZED,
        ),
    ]

    coordinator = InvestmentCommitteeCoordinator()
    verdicts = []

    print("\n--- COMMITTEE DELIBERATION ---")
    for i, deal in enumerate(deals, 1):
        print(f"\nEvaluating Deal #{i}: {deal.title}")
        print(f"  Entry: ${deal.projected_purchase_price:,.0f} | Capex: ${deal.estimated_capex:,.0f} | Exit: ${deal.projected_exit_value:,.0f} ({deal.holding_period_months}m)")
        verdict = coordinator.evaluate_deal(deal, mandate)
        verdicts.append(verdict)

        status_tag = f"[{verdict.verdict.value.upper()}]"
        print(f"  Verdict:           {status_tag}")
        print(f"  IRR / MOIC:        {verdict.underwriting.irr_annualized:.1%} / {verdict.underwriting.moic:.2f}x")
        print(f"  Risk Score:        {verdict.risk.risk_score:.0f}/100 (Downside IRR: {verdict.risk.downside_irr:.1%})")
        print(f"  Rationale:         {verdict.rationale}")
        if verdict.verdict == CommitteeVerdictType.COUNTER_OFFER:
            print(f"  Max Allowable Bid: ${verdict.max_recommended_bid:,.0f} USD (Discount required: {1 - verdict.max_recommended_bid / deal.projected_purchase_price:.1%})")

    # 3. Capital Allocation Decision Table
    print("\n" + "=" * 80)
    print("  PORTFOLIO ALLOCATION SUMMARY: WHERE SHOULD THE NEXT DOLLAR GO?")
    print("=" * 80)
    print(f"{'Opportunity':<36} | {'Verdict':<14} | {'Base IRR':<9} | {'Risk':<8} | {'Recommendation'}")
    print("-" * 80)

    for v, deal in zip(verdicts, deals):
        rec = "Present to investor" if v.verdict == CommitteeVerdictType.APPROVED else (
            f"Offer <= ${v.max_recommended_bid:,.0f}" if v.verdict == CommitteeVerdictType.COUNTER_OFFER else "Pass"
        )
        print(f"{deal.title:<36} | {v.verdict.value.upper():<14} | {v.underwriting.irr_annualized:>7.1%} | {v.risk.risk_score:>5.0f}/100 | {rec}")

    print("=" * 80)


if __name__ == "__main__":
    run_committee_simulation()
