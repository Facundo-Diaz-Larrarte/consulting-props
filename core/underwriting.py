"""Financial Underwriting Engine for Real Estate Capital OS.

Implements deterministic economic modeling:
- Monthly cashflow schedule generation
- Annualized IRR, NPV, MOIC, ROI, Net Profit calculations
- Multi-scenario analysis (Base, Downside, Upside)
- 2D sensitivity matrix (Purchase Price vs. Exit Value)
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple
import numpy_financial as npf

from core.schemas import (
    Opportunity,
    ScenarioMetrics,
    SensitivityPoint,
    UnderwritingModel,
)

DEFAULT_DISCOUNT_RATE_ANNUAL: float = 0.10
DEFAULT_EXIT_TRANSACTION_FEE_PCT: float = 0.04


def build_cashflows(
    purchase_price: float,
    closing_costs_pct: float,
    capex: float,
    holding_period_months: int,
    exit_value: float,
    monthly_gross_rent: float = 0.0,
    monthly_operating_expenses: float = 0.0,
    exit_fee_pct: float = DEFAULT_EXIT_TRANSACTION_FEE_PCT,
) -> List[float]:
    """Generate month-by-month cashflow schedule.

    Month 0: Initial capital deployment (- purchase - closing costs - capex).
    Months 1 .. (holding_period - 1): Net operating rental cashflow.
    Final Month: Net exit proceeds (after transaction fees) + final month operating cashflow.
    """
    duration = max(1, int(holding_period_months))
    total_initial_cost = purchase_price * (1.0 + closing_costs_pct)
    total_capital_required = total_initial_cost + capex

    cashflows: List[float] = [0.0] * (duration + 1)
    cashflows[0] = -round(total_capital_required, 2)

    net_monthly_operating = round(monthly_gross_rent - monthly_operating_expenses, 2)
    for m in range(1, duration):
        cashflows[m] = net_monthly_operating

    net_exit_proceeds = round(exit_value * (1.0 - exit_fee_pct), 2)
    cashflows[duration] = round(net_exit_proceeds + net_monthly_operating, 2)

    return cashflows


def calculate_metrics(
    cashflows: List[float],
    discount_rate_annual: float = DEFAULT_DISCOUNT_RATE_ANNUAL,
) -> Dict[str, float]:
    """Compute deterministic financial return metrics from a cashflow series."""
    # Split inflows and outflows
    total_outflows = abs(cashflows[0]) + sum(abs(cf) for cf in cashflows[1:] if cf < 0)
    total_inflows = sum(cf for cf in cashflows[1:] if cf > 0)

    total_capital_deployed = round(total_outflows, 2)
    net_profit = round(total_inflows - total_outflows, 2)

    if total_outflows > 0:
        moic = round(total_inflows / total_outflows, 4)
        roi = round(net_profit / total_outflows, 4)
    else:
        moic = 0.0
        roi = 0.0

    # Monthly discount rate for compounding: (1 + r_annual)^(1/12) - 1
    if discount_rate_annual > -1.0:
        monthly_discount_rate = (1.0 + discount_rate_annual) ** (1.0 / 12.0) - 1.0
    else:
        monthly_discount_rate = 0.0

    npv_val = float(npf.npv(monthly_discount_rate, cashflows))
    npv = round(npv_val, 2) if not (math.isnan(npv_val) or math.isinf(npv_val)) else 0.0

    # Monthly IRR and Annualized IRR: (1 + monthly_irr)^12 - 1
    try:
        monthly_irr = float(npf.irr(cashflows))
    except Exception:
        monthly_irr = float("nan")

    if math.isnan(monthly_irr) or math.isinf(monthly_irr):
        if total_inflows == 0 and total_outflows > 0:
            irr_annualized = -1.0
        else:
            irr_annualized = 0.0
    elif monthly_irr <= -1.0:
        irr_annualized = -1.0
    else:
        try:
            raw_ann_irr = (1.0 + monthly_irr) ** 12 - 1.0
            if math.isnan(raw_ann_irr) or math.isinf(raw_ann_irr):
                irr_annualized = 0.0
            else:
                irr_annualized = round(raw_ann_irr, 4)
        except (OverflowError, ValueError):
            irr_annualized = 0.0

    return {
        "total_capital_deployed": total_capital_deployed,
        "net_profit": net_profit,
        "irr_annualized": irr_annualized,
        "npv": npv,
        "moic": moic,
        "roi": roi,
    }


def calculate_scenario(
    scenario_name: str,
    purchase_price: float,
    closing_costs_pct: float,
    capex: float,
    holding_period_months: int,
    exit_value: float,
    monthly_gross_rent: float = 0.0,
    monthly_operating_expenses: float = 0.0,
    discount_rate_annual: float = DEFAULT_DISCOUNT_RATE_ANNUAL,
    exit_fee_pct: float = DEFAULT_EXIT_TRANSACTION_FEE_PCT,
) -> ScenarioMetrics:
    """Compute financial metrics for a specific scenario."""
    cashflows = build_cashflows(
        purchase_price=purchase_price,
        closing_costs_pct=closing_costs_pct,
        capex=capex,
        holding_period_months=holding_period_months,
        exit_value=exit_value,
        monthly_gross_rent=monthly_gross_rent,
        monthly_operating_expenses=monthly_operating_expenses,
        exit_fee_pct=exit_fee_pct,
    )
    metrics = calculate_metrics(cashflows, discount_rate_annual=discount_rate_annual)

    return ScenarioMetrics(
        scenario_name=scenario_name,
        exit_value=round(exit_value, 2),
        total_capital_invested=metrics["total_capital_deployed"],
        net_profit=metrics["net_profit"],
        irr_annualized=metrics["irr_annualized"],
        npv=metrics["npv"],
        moic=metrics["moic"],
        roi=metrics["roi"],
    )


def generate_sensitivity_matrix(
    opportunity: Opportunity,
    discount_rate_annual: float = DEFAULT_DISCOUNT_RATE_ANNUAL,
    purchase_price_deltas: Tuple[float, ...] = (-0.10, 0.0, 0.10),
    exit_value_deltas: Tuple[float, ...] = (-0.10, 0.0, 0.10),
    exit_fee_pct: float = DEFAULT_EXIT_TRANSACTION_FEE_PCT,
) -> List[SensitivityPoint]:
    """Generate sensitivity matrix varying purchase price and exit value."""
    points: List[SensitivityPoint] = []
    base_pp = opportunity.projected_purchase_price
    base_ev = opportunity.projected_exit_value
    capex = opportunity.estimated_capex
    duration = opportunity.holding_period_months

    for pp_delta in purchase_price_deltas:
        pp = round(base_pp * (1.0 + pp_delta), 2)
        for ev_delta in exit_value_deltas:
            ev = round(base_ev * (1.0 + ev_delta), 2)
            cfs = build_cashflows(
                purchase_price=pp,
                closing_costs_pct=opportunity.closing_costs_pct,
                capex=capex,
                holding_period_months=duration,
                exit_value=ev,
                monthly_gross_rent=opportunity.monthly_gross_rent,
                monthly_operating_expenses=opportunity.monthly_operating_expenses,
                exit_fee_pct=exit_fee_pct,
            )
            m = calculate_metrics(cfs, discount_rate_annual=discount_rate_annual)
            points.append(
                SensitivityPoint(
                    purchase_price=pp,
                    exit_value=ev,
                    capex=round(capex, 2),
                    holding_period_months=duration,
                    irr_annualized=m["irr_annualized"],
                    moic=m["moic"],
                    npv=m["npv"],
                )
            )

    return points


def run_underwriting(
    opportunity: Opportunity,
    discount_rate_annual: float = DEFAULT_DISCOUNT_RATE_ANNUAL,
    exit_fee_pct: float = DEFAULT_EXIT_TRANSACTION_FEE_PCT,
) -> UnderwritingModel:
    """Run full deterministic financial underwriting on an opportunity."""
    # 1. Base Scenario Cashflows & Metrics
    base_cashflows = build_cashflows(
        purchase_price=opportunity.projected_purchase_price,
        closing_costs_pct=opportunity.closing_costs_pct,
        capex=opportunity.estimated_capex,
        holding_period_months=opportunity.holding_period_months,
        exit_value=opportunity.projected_exit_value,
        monthly_gross_rent=opportunity.monthly_gross_rent,
        monthly_operating_expenses=opportunity.monthly_operating_expenses,
        exit_fee_pct=exit_fee_pct,
    )
    base_metrics = calculate_metrics(base_cashflows, discount_rate_annual=discount_rate_annual)

    base_scenario = ScenarioMetrics(
        scenario_name="Base",
        exit_value=round(opportunity.projected_exit_value, 2),
        total_capital_invested=base_metrics["total_capital_deployed"],
        net_profit=base_metrics["net_profit"],
        irr_annualized=base_metrics["irr_annualized"],
        npv=base_metrics["npv"],
        moic=base_metrics["moic"],
        roi=base_metrics["roi"],
    )

    # 2. Downside Scenario: exit * 0.85, capex * 1.20, duration + 3
    downside_scenario = calculate_scenario(
        scenario_name="Downside",
        purchase_price=opportunity.projected_purchase_price,
        closing_costs_pct=opportunity.closing_costs_pct,
        capex=opportunity.estimated_capex * 1.20,
        holding_period_months=opportunity.holding_period_months + 3,
        exit_value=opportunity.projected_exit_value * 0.85,
        monthly_gross_rent=opportunity.monthly_gross_rent,
        monthly_operating_expenses=opportunity.monthly_operating_expenses,
        discount_rate_annual=discount_rate_annual,
        exit_fee_pct=exit_fee_pct,
    )

    # 3. Upside Scenario: exit * 1.10, capex * 0.95, duration max(1, duration - 1)
    upside_scenario = calculate_scenario(
        scenario_name="Upside",
        purchase_price=opportunity.projected_purchase_price,
        closing_costs_pct=opportunity.closing_costs_pct,
        capex=opportunity.estimated_capex * 0.95,
        holding_period_months=max(1, opportunity.holding_period_months - 1),
        exit_value=opportunity.projected_exit_value * 1.10,
        monthly_gross_rent=opportunity.monthly_gross_rent,
        monthly_operating_expenses=opportunity.monthly_operating_expenses,
        discount_rate_annual=discount_rate_annual,
        exit_fee_pct=exit_fee_pct,
    )

    scenarios: Dict[str, ScenarioMetrics] = {
        "Base": base_scenario,
        "Downside": downside_scenario,
        "Upside": upside_scenario,
    }

    # 4. Sensitivity Matrix
    sensitivities = generate_sensitivity_matrix(
        opportunity=opportunity,
        discount_rate_annual=discount_rate_annual,
        exit_fee_pct=exit_fee_pct,
    )

    return UnderwritingModel(
        opportunity_id=opportunity.id,
        discount_rate_annual=discount_rate_annual,
        total_capital_deployed=base_metrics["total_capital_deployed"],
        net_profit=base_metrics["net_profit"],
        irr_annualized=base_metrics["irr_annualized"],
        npv=base_metrics["npv"],
        moic=base_metrics["moic"],
        roi=base_metrics["roi"],
        monthly_cashflows=base_cashflows,
        scenarios=scenarios,
        sensitivities=sensitivities,
    )
