import sys
from pathlib import Path

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from core.schemas import Opportunity, StrategyType
from core.underwriting import (
    DEFAULT_DISCOUNT_RATE_ANNUAL,
    DEFAULT_EXIT_TRANSACTION_FEE_PCT,
    build_cashflows,
    calculate_metrics,
    run_underwriting,
)


@pytest.fixture
def sample_renovate_deal() -> Opportunity:
    """Standard renovate and sell opportunity in Cordoba."""
    return Opportunity(
        title="Nueva Cordoba 2BR Renovation",
        location="Cordoba, Argentina",
        strategy=StrategyType.RENOVATE_AND_SELL,
        asking_price=90000.0,
        projected_purchase_price=80000.0,
        estimated_capex=20000.0,
        closing_costs_pct=0.06,
        holding_period_months=6,
        projected_exit_value=130000.0,
        monthly_gross_rent=0.0,
        monthly_operating_expenses=0.0,
    )


@pytest.fixture
def sample_rental_deal() -> Opportunity:
    """Standard buy and hold rental opportunity with monthly operating flows."""
    return Opportunity(
        title="General Paz 1BR Rental",
        location="Cordoba, Argentina",
        strategy=StrategyType.BUY_AND_HOLD,
        asking_price=65000.0,
        projected_purchase_price=60000.0,
        estimated_capex=5000.0,
        closing_costs_pct=0.06,
        holding_period_months=12,
        projected_exit_value=75000.0,
        monthly_gross_rent=600.0,
        monthly_operating_expenses=150.0,
    )


class TestCashflowConstruction:
    """Verify month-by-month cashflow arrays."""

    def test_build_cashflows_zero_rent(self, sample_renovate_deal: Opportunity):
        cfs = build_cashflows(
            purchase_price=sample_renovate_deal.projected_purchase_price,
            closing_costs_pct=sample_renovate_deal.closing_costs_pct,
            capex=sample_renovate_deal.estimated_capex,
            holding_period_months=sample_renovate_deal.holding_period_months,
            exit_value=sample_renovate_deal.projected_exit_value,
        )
        # 6-month deal -> indices 0 through 6 (length 7)
        assert len(cfs) == 7
        # Month 0: -(80000 * 1.06 + 20000) = -104800.0
        assert cfs[0] == -104800.0
        # Months 1 to 5: 0.0
        for m in range(1, 6):
            assert cfs[m] == 0.0
        # Month 6: 130000 * 0.96 = 124800.0
        assert cfs[6] == 124800.0

    def test_build_cashflows_with_rent(self, sample_rental_deal: Opportunity):
        cfs = build_cashflows(
            purchase_price=sample_rental_deal.projected_purchase_price,
            closing_costs_pct=sample_rental_deal.closing_costs_pct,
            capex=sample_rental_deal.estimated_capex,
            holding_period_months=sample_rental_deal.holding_period_months,
            exit_value=sample_rental_deal.projected_exit_value,
            monthly_gross_rent=sample_rental_deal.monthly_gross_rent,
            monthly_operating_expenses=sample_rental_deal.monthly_operating_expenses,
        )
        # 12-month deal -> length 13
        assert len(cfs) == 13
        # Month 0: -(60000 * 1.06 + 5000) = -68600.0
        assert cfs[0] == -68600.0
        # Months 1 to 11: net rent = 600 - 150 = 450.0
        for m in range(1, 12):
            assert cfs[m] == 450.0
        # Month 12: net exit (75000 * 0.96 = 72000) + final month rent (450) = 72450.0
        assert cfs[12] == 72450.0


class TestUnderwritingBaseMetrics:
    """Verify base buy & sell / renovate & sell deal produces positive IRR, correct MOIC and NPV."""

    def test_renovate_deal_underwriting_metrics(self, sample_renovate_deal: Opportunity):
        model = run_underwriting(sample_renovate_deal, discount_rate_annual=0.10)

        # Expected capital: 80,000 * 1.06 + 20,000 = 104,800
        assert model.total_capital_deployed == 104800.0

        # Expected exit: 130,000 * (1 - 0.04) = 124,800
        # Net profit: 124,800 - 104,800 = 20,000
        assert model.net_profit == 20000.0

        # MOIC: 124,800 / 104,800 ~= 1.1908
        assert model.moic == pytest.approx(1.1908, abs=1e-4)

        # ROI: 20,000 / 104,800 ~= 0.1908
        assert model.roi == pytest.approx(0.1908, abs=1e-4)
        assert model.moic == pytest.approx(1.0 + model.roi, abs=1e-4)

        # Annualized IRR: (124800 / 104800)**(12/6) - 1 ~= 0.4181 (41.81%)
        assert model.irr_annualized > 0.40
        assert model.irr_annualized == pytest.approx(0.4181, abs=1e-3)

        # NPV at 10%: positive
        assert model.npv > 0
        assert model.npv == pytest.approx(14192.13, abs=5.0)

        # Monthly cashflows match length
        assert len(model.monthly_cashflows) == 7

    def test_rental_deal_underwriting_metrics(self, sample_rental_deal: Opportunity):
        model = run_underwriting(sample_rental_deal, discount_rate_annual=0.10)

        # Capital: 60000 * 1.06 + 5000 = 68600.0
        assert model.total_capital_deployed == 68600.0

        # Inflows: 11 * 450 + 72450 = 77400.0
        # Net profit: 77400 - 68600 = 8800.0
        assert model.net_profit == 8800.0
        assert model.moic == pytest.approx(77400.0 / 68600.0, abs=1e-4)
        assert model.irr_annualized > 0
        assert model.npv > 0


class TestScenarioRelations:
    """Verify Downside and Upside scenario relations (Upside IRR > Base IRR > Downside IRR)."""

    def test_scenario_hierarchy(self, sample_renovate_deal: Opportunity):
        model = run_underwriting(sample_renovate_deal, discount_rate_annual=0.10)

        assert "Base" in model.scenarios
        assert "Downside" in model.scenarios
        assert "Upside" in model.scenarios

        base = model.scenarios["Base"]
        downside = model.scenarios["Downside"]
        upside = model.scenarios["Upside"]

        # IRR ordering: Upside > Base > Downside
        assert upside.irr_annualized > base.irr_annualized > downside.irr_annualized

        # NPV ordering: Upside > Base > Downside
        assert upside.npv > base.npv > downside.npv

        # MOIC ordering: Upside > Base > Downside
        assert upside.moic > base.moic > downside.moic

        # Net Profit ordering: Upside > Base > Downside
        assert upside.net_profit > base.net_profit > downside.net_profit

    def test_scenario_parameter_adjustments(self, sample_renovate_deal: Opportunity):
        model = run_underwriting(sample_renovate_deal)

        base = model.scenarios["Base"]
        downside = model.scenarios["Downside"]
        upside = model.scenarios["Upside"]

        # Exit values: Downside = 85%, Base = 100%, Upside = 110%
        assert downside.exit_value == pytest.approx(sample_renovate_deal.projected_exit_value * 0.85, abs=0.01)
        assert base.exit_value == pytest.approx(sample_renovate_deal.projected_exit_value, abs=0.01)
        assert upside.exit_value == pytest.approx(sample_renovate_deal.projected_exit_value * 1.10, abs=0.01)

        # Capital invested: Downside has 20% higher capex, Upside has 5% lower capex
        initial_cost = sample_renovate_deal.projected_purchase_price * (1.0 + sample_renovate_deal.closing_costs_pct)
        assert downside.total_capital_invested == pytest.approx(initial_cost + sample_renovate_deal.estimated_capex * 1.20, abs=0.01)
        assert base.total_capital_invested == pytest.approx(initial_cost + sample_renovate_deal.estimated_capex, abs=0.01)
        assert upside.total_capital_invested == pytest.approx(initial_cost + sample_renovate_deal.estimated_capex * 0.95, abs=0.01)


class TestSensitivityMatrix:
    """Verify sensitivity points are properly populated and monotonic."""

    def test_sensitivity_points_count_and_schema(self, sample_renovate_deal: Opportunity):
        model = run_underwriting(sample_renovate_deal)

        # 3 purchase price deltas x 3 exit value deltas = 9 points
        assert len(model.sensitivities) == 9

        base_pp = sample_renovate_deal.projected_purchase_price
        base_ev = sample_renovate_deal.projected_exit_value

        expected_pps = {round(base_pp * 0.90, 2), round(base_pp * 1.0, 2), round(base_pp * 1.10, 2)}
        expected_evs = {round(base_ev * 0.90, 2), round(base_ev * 1.0, 2), round(base_ev * 1.10, 2)}

        actual_pps = {p.purchase_price for p in model.sensitivities}
        actual_evs = {p.exit_value for p in model.sensitivities}

        assert actual_pps == expected_pps
        assert actual_evs == expected_evs

    def test_sensitivity_monotonicity(self, sample_renovate_deal: Opportunity):
        model = run_underwriting(sample_renovate_deal)

        # For a fixed purchase price, higher exit value must yield higher IRR and MOIC
        base_pp = sample_renovate_deal.projected_purchase_price
        points_at_base_pp = [p for p in model.sensitivities if p.purchase_price == base_pp]
        points_at_base_pp.sort(key=lambda p: p.exit_value)

        assert len(points_at_base_pp) == 3
        assert points_at_base_pp[0].irr_annualized < points_at_base_pp[1].irr_annualized < points_at_base_pp[2].irr_annualized
        assert points_at_base_pp[0].moic < points_at_base_pp[1].moic < points_at_base_pp[2].moic
        assert points_at_base_pp[0].npv < points_at_base_pp[1].npv < points_at_base_pp[2].npv

        # For a fixed exit value, higher purchase price must yield lower IRR and MOIC
        base_ev = sample_renovate_deal.projected_exit_value
        points_at_base_ev = [p for p in model.sensitivities if p.exit_value == base_ev]
        points_at_base_ev.sort(key=lambda p: p.purchase_price)

        assert len(points_at_base_ev) == 3
        assert points_at_base_ev[0].irr_annualized > points_at_base_ev[1].irr_annualized > points_at_base_ev[2].irr_annualized
        assert points_at_base_ev[0].moic > points_at_base_ev[1].moic > points_at_base_ev[2].moic
        assert points_at_base_ev[0].npv > points_at_base_ev[1].npv > points_at_base_ev[2].npv


class TestEdgeCases:
    """Verify stability under boundary conditions."""

    def test_one_month_holding_period(self):
        opp = Opportunity(
            title="Fast Flip",
            location="Cordoba",
            asking_price=50000.0,
            projected_purchase_price=45000.0,
            estimated_capex=2000.0,
            closing_costs_pct=0.04,
            holding_period_months=1,
            projected_exit_value=55000.0,
        )
        model = run_underwriting(opp)
        assert len(model.monthly_cashflows) == 2
        # Upside duration max(1, 1 - 1) = 1
        assert "Upside" in model.scenarios
        assert model.scenarios["Upside"].irr_annualized > 0

    def test_loss_making_deal(self):
        opp = Opportunity(
            title="Underwater Deal",
            location="Cordoba",
            asking_price=100000.0,
            projected_purchase_price=100000.0,
            estimated_capex=30000.0,
            closing_costs_pct=0.06,
            holding_period_months=12,
            projected_exit_value=80000.0,
        )
        model = run_underwriting(opp)
        assert model.net_profit < 0
        assert model.moic < 1.0
        assert model.roi < 0
        assert model.npv < 0
        assert model.irr_annualized < 0

    def test_discount_rate_sensitivity(self, sample_renovate_deal: Opportunity):
        model_low_dr = run_underwriting(sample_renovate_deal, discount_rate_annual=0.05)
        model_high_dr = run_underwriting(sample_renovate_deal, discount_rate_annual=0.15)

        # Higher discount rate must produce lower NPV
        assert model_low_dr.npv > model_high_dr.npv
        # IRR and MOIC must be independent of the discount rate
        assert model_low_dr.irr_annualized == model_high_dr.irr_annualized
        assert model_low_dr.moic == model_high_dr.moic

    def test_total_loss_cashflow_handling(self):
        # Edge case: zero inflows in cashflows
        m = calculate_metrics([-100000.0, 0.0, 0.0])
        assert m["total_capital_deployed"] == 100000.0
        assert m["net_profit"] == -100000.0
        assert m["moic"] == 0.0
        assert m["roi"] == -1.0
        assert m["irr_annualized"] == -1.0
        assert m["npv"] == -100000.0

