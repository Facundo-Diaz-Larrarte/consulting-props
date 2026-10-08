"""Unit and functional tests for Platform Monetization and Unit Economics (Sections 21 & 22)."""

import pytest
from core.monetization import (
    DealMonetization,
    FeeBreakdown,
    FeeScheduleConfig,
    NetInvestorMetrics,
    PlatformUnitEconomics,
    calculate_deal_monetization,
)
from core.memo import generate_investment_memo
from core.schemas import Opportunity, StrategyType
from core.underwriting import run_underwriting


@pytest.fixture
def sample_profitable_opportunity() -> Opportunity:
    """A standard high-yielding buy & sell deal (IRR well above 12% hurdle)."""
    return Opportunity(
        title="Departamento Recoleta Flip",
        location="Recoleta, CABA",
        strategy=StrategyType.RENOVATE_AND_SELL,
        asking_price=100000.0,
        projected_purchase_price=90000.0,
        closing_costs_pct=0.04,  # $3,600
        estimated_capex=10000.0,
        projected_exit_value=135000.0,
        holding_period_months=6,
        monthly_gross_rent=0.0,
        monthly_operating_expenses=0.0,
    )


@pytest.fixture
def sample_marginal_opportunity() -> Opportunity:
    """A low-yielding deal whose return does not clear the 12% annual hurdle."""
    return Opportunity(
        title="Cochera Microcentro Renta Baja",
        location="Microcentro, CABA",
        strategy=StrategyType.BUY_AND_HOLD,
        asking_price=20000.0,
        projected_purchase_price=20000.0,
        closing_costs_pct=0.05,  # $1,000
        estimated_capex=0.0,
        projected_exit_value=20500.0,
        holding_period_months=12,
        monthly_gross_rent=100.0,
        monthly_operating_expenses=40.0,  # net $60/month = $720/year
    )


def test_standard_fee_schedule_calculation(sample_profitable_opportunity: Opportunity):
    underwriting = run_underwriting(sample_profitable_opportunity)
    mon = calculate_deal_monetization(sample_profitable_opportunity, underwriting)

    # 1.5% of 90,000 = 1,350
    assert mon.fee_breakdown.origination_fee == pytest.approx(1350.0, abs=1e-2)
    # 1.0% of total_capital_required (90,000 + 3,600 + 10,000 = 103,600) = 1,036
    assert mon.fee_breakdown.structuring_fee == pytest.approx(1036.0, abs=1e-2)
    # 1.5% of 135,000 exit = 2,025
    assert mon.fee_breakdown.success_fee == pytest.approx(2025.0, abs=1e-2)
    # Deal is highly profitable -> performance fee should be positive
    assert mon.fee_breakdown.performance_fee > 0.0
    assert mon.carry_earned == mon.fee_breakdown.performance_fee


def test_no_carry_when_below_hurdle(sample_marginal_opportunity: Opportunity):
    underwriting = run_underwriting(sample_marginal_opportunity)
    mon = calculate_deal_monetization(sample_marginal_opportunity, underwriting)

    # Return is low (< 12%), so performance fee / carry must be strictly zero
    assert mon.fee_breakdown.performance_fee == 0.0
    assert mon.carry_earned == 0.0
    # Total platform revenue consists only of fixed upfront & success fees
    expected_rev = (
        mon.fee_breakdown.origination_fee
        + mon.fee_breakdown.structuring_fee
        + mon.fee_breakdown.success_fee
    )
    assert mon.fee_breakdown.total_platform_revenue == pytest.approx(expected_rev, abs=1e-2)


def test_carry_waterfall_preserves_hurdle_incentive(sample_profitable_opportunity: Opportunity):
    underwriting = run_underwriting(sample_profitable_opportunity)
    mon = calculate_deal_monetization(sample_profitable_opportunity, underwriting)

    # Investor Net IRR must be lower than Gross IRR due to platform fees and carry
    assert mon.net_investor_metrics.net_irr_annualized < underwriting.irr_annualized
    # Investor Net MOIC must be lower than Gross MOIC
    assert mon.net_investor_metrics.net_moic < underwriting.moic
    # Net IRR must still beat the hurdle since the deal had substantial upside
    assert mon.net_investor_metrics.net_irr_annualized > mon.hurdle_rate_annual


def test_platform_unit_economics_metrics(sample_profitable_opportunity: Opportunity):
    underwriting = run_underwriting(sample_profitable_opportunity)
    mon = calculate_deal_monetization(sample_profitable_opportunity, underwriting)

    ue = mon.unit_economics
    # GMV = purchase_price + capex + exit_value = 90k + 10k + 135k = 235k
    expected_gmv = 90000.0 + 10000.0 + 135000.0
    assert ue.gmv == pytest.approx(expected_gmv, abs=1.0)

    # Effective take rate = total_platform_revenue / GMV
    assert ue.effective_take_rate == pytest.approx(ue.platform_revenue / ue.gmv, abs=1e-4)
    assert 0.01 < ue.effective_take_rate < 0.15  # within institutional market parameters

    # Direct costs = 15% of revenue, Contribution Margin = 85% of revenue
    assert ue.direct_costs == pytest.approx(ue.platform_revenue * 0.15, abs=1e-2)
    assert ue.contribution_margin == pytest.approx(ue.platform_revenue - ue.direct_costs, abs=1e-2)
    assert ue.contribution_margin_pct == pytest.approx(0.85, abs=1e-4)


def test_custom_fee_schedule_configuration(sample_profitable_opportunity: Opportunity):
    underwriting = run_underwriting(sample_profitable_opportunity)
    custom_cfg = FeeScheduleConfig(
        origination_fee_pct=0.02,  # 2.0%
        structuring_fee_pct=0.0,   # 0.0%
        success_fee_pct=0.01,      # 1.0%
        carry_percentage=0.10,     # 10%
        hurdle_rate_annual=0.15,   # 15% hurdle
        direct_cost_pct_of_revenue=0.10,
    )
    mon = calculate_deal_monetization(sample_profitable_opportunity, underwriting, config=custom_cfg)

    assert mon.fee_breakdown.origination_fee == pytest.approx(90000.0 * 0.02, abs=1e-2)
    assert mon.fee_breakdown.structuring_fee == 0.0
    assert mon.fee_breakdown.success_fee == pytest.approx(135000.0 * 0.01, abs=1e-2)
    assert mon.hurdle_rate_annual == 0.15
    assert mon.unit_economics.contribution_margin_pct == pytest.approx(0.90, abs=1e-4)


def test_investment_memo_displays_monetization_section(sample_profitable_opportunity: Opportunity):
    underwriting = run_underwriting(sample_profitable_opportunity)
    memo = generate_investment_memo(sample_profitable_opportunity, underwriting)

    assert "## 6. Platform Fees & Net Investor Yield (Sections 21 & 22)" in memo.markdown_content
    assert "Origination Fee" in memo.markdown_content
    assert "Structuring Fee" in memo.markdown_content
    assert "Success Fee" in memo.markdown_content
    assert "Performance Fee (Carry)" in memo.markdown_content
    assert "Total Platform Revenue" in memo.markdown_content
    assert "Investor Net IRR" in memo.markdown_content
    assert "Investor Net MOIC" in memo.markdown_content
