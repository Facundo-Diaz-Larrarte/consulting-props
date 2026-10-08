"""Investment Memo generator for Real Estate Capital OS.

Implements Section 15 of Master Project Document:
Standardized, institutional investment memorandum generation.
"""

from __future__ import annotations

from typing import List, Optional
from core.schemas import InvestmentMemo, Opportunity, UnderwritingModel
from core.monetization import DealMonetization, calculate_deal_monetization


def generate_investment_memo(
    opportunity: Opportunity,
    underwriting: UnderwritingModel,
    thesis: Optional[str] = None,
    key_risks: Optional[List[str]] = None,
    exit_strategy: Optional[str] = None,
    monetization: Optional[DealMonetization] = None,
) -> InvestmentMemo:
    """Build a structured and human-readable Investment Memo from an Opportunity and UnderwritingModel."""
    
    # Default qualitative thesis if not supplied
    resolved_thesis = thesis or (
        f"Adquisición de activo en {opportunity.location} bajo estrategia {opportunity.strategy.value.replace('_', ' ').title()}. "
        f"Entrada a precio negociado (${opportunity.projected_purchase_price:,.0f} vs ${opportunity.asking_price:,.0f} asking), "
        f"con valor agregado estimado en ${opportunity.estimated_capex:,.0f} de capex para capturar un precio de salida de ${opportunity.projected_exit_value:,.0f}."
    )

    resolved_risks = key_risks or [
        "Riesgo de ejecución: Desvíos en costos o tiempos de obra/reforma.",
        "Riesgo de liquidez y mercado: Menor demanda o mayor tiempo de venta al precio objetivo.",
        "Riesgo cambiario / macroeconómico: Volatilidad en costos de reposición en pesos/dólares.",
    ]

    resolved_exit = exit_strategy or (
        f"Venta en el mercado abierto con corretaje local a un valor proyectado de ${opportunity.projected_exit_value:,.0f} "
        f"tras un período de maduración/obra de {opportunity.holding_period_months} meses."
    )

    downside = underwriting.scenarios.get("downside")
    base = underwriting.scenarios.get("base")
    upside = underwriting.scenarios.get("upside")

    scenarios_summary = (
        f"Base IRR: {underwriting.irr_annualized:.1%} (MOIC: {underwriting.moic:.2f}x) | "
        f"Downside IRR: {downside.irr_annualized if downside else 0.0:.1%} (MOIC: {downside.moic if downside else 0.0:.2f}x) | "
        f"Upside IRR: {upside.irr_annualized if upside else 0.0:.1%} (MOIC: {upside.moic if upside else 0.0:.2f}x)"
    )

    # Generate Markdown representation
    md_lines = [
        f"# INVESTMENT MEMORANDUM: {opportunity.title.upper()}",
        f"**Location:** {opportunity.location} | **Strategy:** {opportunity.strategy.value.replace('_', ' ').title()} | **Status:** {opportunity.status.value.upper()}",
        "",
        "---",
        "",
        "## 1. Executive Overview",
        f"- **Asset:** {opportunity.title}",
        f"- **Location:** {opportunity.location}",
        f"- **Target Strategy:** {opportunity.strategy.value.replace('_', ' ').title()}",
        f"- **Holding Period:** {opportunity.holding_period_months} months",
        f"- **Total Capital Required:** ${opportunity.total_capital_required:,.0f} USD",
        "",
        "## 2. Investment Thesis",
        resolved_thesis,
        "",
        "## 3. Financial Architecture & Economics",
        "| Line Item | Amount (USD) | Notes |",
        "| :--- | :--- | :--- |",
        f"| Asking Price | ${opportunity.asking_price:,.0f} | List price |",
        f"| Projected Purchase Price | ${opportunity.projected_purchase_price:,.0f} | Acquisition target |",
        f"| Closing & Legal Costs ({opportunity.closing_costs_pct:.1%}) | ${opportunity.projected_purchase_price * opportunity.closing_costs_pct:,.0f} | Notary, taxes, legal |",
        f"| Estimated Capex | ${opportunity.estimated_capex:,.0f} | Renovations / repositioning |",
        f"| **Total Capital Deployed** | **${opportunity.total_capital_required:,.0f}** | Equity deployment |",
        f"| Projected Exit Value | ${opportunity.projected_exit_value:,.0f} | Target gross realization |",
        f"| Projected Net Profit | ${underwriting.net_profit:,.0f} | Net cash proceeds |",
        "",
        "## 4. Return Profile & Core Metrics",
        f"- **Annualized IRR:** {underwriting.irr_annualized:.1%}",
        f"- **MOIC (Equity Multiple):** {underwriting.moic:.2f}x",
        f"- **ROI on Deployed Capital:** {underwriting.roi:.1%}",
        f"- **NPV (Discount rate {underwriting.discount_rate_annual:.1%}):** ${underwriting.npv:,.0f} USD",
        "",
        "## 5. Scenario Analysis",
        "| Scenario | Exit Value | Capital Invested | Net Profit | IRR (Ann.) | MOIC |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for sc_name, sc in underwriting.scenarios.items():
        md_lines.append(
            f"| **{sc_name.capitalize()}** | ${sc.exit_value:,.0f} | ${sc.total_capital_invested:,.0f} | ${sc.net_profit:,.0f} | {sc.irr_annualized:.1%} | {sc.moic:.2f}x |"
        )

    mon = monetization or calculate_deal_monetization(opportunity, underwriting)

    md_lines.extend([
        "",
        "## 6. Platform Fees & Net Investor Yield (Sections 21 & 22)",
        "| Fee / Metric | Amount / Rate | Timing |",
        "| :--- | :--- | :--- |",
        f"| Origination Fee | ${mon.fee_breakdown.origination_fee:,.0f} | Entry |",
        f"| Structuring Fee | ${mon.fee_breakdown.structuring_fee:,.0f} | Entry |",
        f"| Success Fee | ${mon.fee_breakdown.success_fee:,.0f} | Exit |",
        f"| Performance Fee (Carry) | ${mon.fee_breakdown.performance_fee:,.0f} | Exit (Hurdle {mon.hurdle_rate_annual:.1%}) |",
        f"| **Total Platform Revenue** | **${mon.fee_breakdown.total_platform_revenue:,.0f}** | Effective Take Rate: {mon.unit_economics.effective_take_rate:.2%} |",
        f"| **Investor Net IRR** | **{mon.net_investor_metrics.net_irr_annualized:.1%}** | Net of all platform fees |",
        f"| **Investor Net MOIC** | **{mon.net_investor_metrics.net_moic:.2f}x** | Net equity multiple |",
        "",
        "## 7. Key Risks & Mitigants",
    ])
    for risk in resolved_risks:
        md_lines.append(f"- {risk}")

    md_lines.extend([
        "",
        "## 8. Exit Strategy",
        resolved_exit,
        "",
        "---",
        f"*Generated automatically by Real Estate Capital OS Underwriting Core on {underwriting.calculated_at.strftime('%Y-%m-%d')}*",
    ])

    full_markdown = "\n".join(md_lines)

    return InvestmentMemo(
        opportunity_id=opportunity.id,
        title=f"Memo: {opportunity.title}",
        target_geography=opportunity.location,
        strategy=opportunity.strategy,
        capital_required=opportunity.total_capital_required,
        projected_holding_months=opportunity.holding_period_months,
        target_irr=underwriting.irr_annualized,
        target_moic=underwriting.moic,
        npv=underwriting.npv,
        thesis=resolved_thesis,
        scenarios_summary=scenarios_summary,
        key_risks=resolved_risks,
        exit_strategy=resolved_exit,
        markdown_content=full_markdown,
    )
