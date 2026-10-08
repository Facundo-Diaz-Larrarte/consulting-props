"""End-to-End Pilot Deal Demonstration for Real Estate Capital OS.

Implements Sections 20 & 44:
Runs the entire deal cycle from Investor Mandate to Sourcing, Underwriting,
Investment Memo generation, and Pipeline tracking.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.agents.ingestion import PropertyIngestionAgent
from core.memo import generate_investment_memo
from core.schemas import (
    DealPipelineItem,
    DealStage,
    InvestorMandate,
    RiskTolerance,
    StrategyType,
)
from core.underwriting import run_underwriting


def run_pilot():
    print("=" * 70)
    print("  REAL ESTATE CAPITAL OS — PILOT DEAL EXECUTION ENGINE (CORDOBA)")
    print("=" * 70)

    # 1. Investor Mandate (Object 1)
    print("\n[1/5] Defining Investor Mandate...")
    mandate = InvestorMandate(
        investor_name="Grupo Inversor Mediterraneo",
        capital_available=300000.0,
        currency="USD",
        target_irr=0.16,
        investment_horizon_months=18,
        risk_tolerance=RiskTolerance.MEDIUM,
        geography=["Cordoba"],
        strategies=[StrategyType.RENOVATE_AND_SELL],
    )
    print(f"  Investor: {mandate.investor_name}")
    print(f"  Capital Available: ${mandate.capital_available:,.0f} USD")
    print(f"  Target IRR: {mandate.target_irr:.1%} | Horizon: {mandate.investment_horizon_months} months")

    # 2. Raw Sourcing & AI Normalization (Object 2)
    print("\n[2/5] Ingesting Unstructured Broker Deal...")
    raw_broker_message = (
        "OPORTUNIDAD EXCLUSIVA NUEVA CORDOBA: Semipiso sobre calle Rondeau a 2 cuadras de Plaza Espana. "
        "Piden USD 95.000 pero se conversa a USD 82.000 de contado. "
        "Con USD 18.000 de reforma de diseno (cocina integrada, sanitarios nuevos, aberturas) "
        "se revaloriza para venderse en USD 140.000 en un plazo de 12 meses. Excelente producto flip."
    )
    print(f'  Input text: "{raw_broker_message[:90]}..."')

    agent = PropertyIngestionAgent()
    opportunity = agent.ingest(raw_broker_message)

    print(f"  Normalized Asset: {opportunity.title}")
    print(f"  Location: {opportunity.location}")
    print(f"  Strategy: {opportunity.strategy.value}")
    print(f"  Projected Acquisition: ${opportunity.projected_purchase_price:,.0f} (Asking: ${opportunity.asking_price:,.0f})")
    print(f"  Capex: ${opportunity.estimated_capex:,.0f}")
    print(f"  Total Capital Required: ${opportunity.total_capital_required:,.0f} USD")

    # 3. Pipeline Initial Registration (Object 5)
    print("\n[3/5] Tracking Deal Pipeline...")
    pipeline_item = DealPipelineItem(
        opportunity_id=opportunity.id,
        mandate_id=mandate.id,
        current_stage=DealStage.NORMALIZED,
    )
    pipeline_item.transition_to(DealStage.UNDERWRITTEN, reason="Passed initial screening, running quantitative underwriting")
    print(f"  Current Stage: {pipeline_item.current_stage.value.upper()}")

    # 4. Deterministic Underwriting (Object 3)
    print("\n[4/5] Executing Quantitative Underwriting Engine...")
    underwriting = run_underwriting(opportunity, discount_rate_annual=0.10)

    print(f"  Annualized IRR: {underwriting.irr_annualized:.1%} (Target: {mandate.target_irr:.1%})")
    print(f"  MOIC (Equity Multiple): {underwriting.moic:.2f}x")
    print(f"  Net Cash Profit: ${underwriting.net_profit:,.0f} USD")
    print(f"  NPV @ 10%: ${underwriting.npv:,.0f} USD")
    print("  Scenario Comparison:")
    for name, sc in underwriting.scenarios.items():
        print(f"    - {name.capitalize():<8}: Exit ${sc.exit_value:,.0f} | Profit ${sc.net_profit:,.0f} | IRR {sc.irr_annualized:.1%} | MOIC {sc.moic:.2f}x")

    is_qualified = underwriting.irr_annualized >= mandate.target_irr
    if is_qualified:
        pipeline_item.transition_to(DealStage.APPROVED, reason="IRR surpasses investor hurdle rate")
        print("\n  >>> STATUS: DEAL APPROVED FOR INVESTMENT COMMITTEE & PRESENTATION <<<")
    else:
        print("\n  >>> STATUS: DEAL BELOW HURDLE RATE <<<")

    # 5. Investment Memo Generation (Object 4)
    print("\n[5/5] Generating Institutional Investment Memo...")
    output_dir = Path(__file__).resolve().parent.parent / "memos"
    output_dir.mkdir(exist_ok=True)
    memo_file = output_dir / "memo_pilot_cordoba_rondeau.md"

    memo = generate_investment_memo(
        opportunity=opportunity,
        underwriting=underwriting,
        thesis=(
            "Adquisición de semipiso con descuento por necesidad de reforma cosmética integral en Nueva Córdoba. "
            "La zona exhibe absorción récord de unidades de 2 dormitorios premium para inversores de renta y profesionales. "
            "La reforma de diseño desbloquea el diferencial de precio por m² terminado."
        ),
        key_risks=[
            "Riesgo de obra: Posible desvío de costos en refacción de cañerías y aberturas (+15% cubierto en Downside).",
            "Riesgo de mercado: Estiramiento de plazo de comercialización a 15 meses.",
            "Riesgo de escrituración: Retraso en tracto abreviado.",
        ],
        exit_strategy="Comercialización mediante red de brokers aliados en Córdoba Capital con precio de salida de USD 140.000.",
    )

    memo_file.write_text(memo.markdown_content, encoding="utf-8")
    print(f"  Memo written to: {memo_file.relative_to(Path.cwd())}")

    pipeline_item.transition_to(DealStage.PRESENTED, reason=f"Memo generated and ready for presentation to {mandate.investor_name}")
    print(f"  Pipeline Final Stage: {pipeline_item.current_stage.value.upper()}")
    print("\n" + "=" * 70)
    print("  CYCLE COMPLETE: DEPLOYABLE CAPITAL SUCCESSFULLY MATCHED & UNDERWRITTEN")
    print("=" * 70)


if __name__ == "__main__":
    run_pilot()
