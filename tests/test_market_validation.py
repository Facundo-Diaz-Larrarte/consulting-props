import sys
from pathlib import Path

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from core.schemas import InvestorMandate, Opportunity, RiskTolerance, StrategyType
from core.tools.idecor import (
    IDECOR_OMI_BENCHMARKS,
    audit_property_valuation,
    resolve_neighborhood,
)
from core.agents.committee import RiskAgent, UnderwritingAgent
from core.agents.langgraph_committee import run_langgraph_committee
from core.underwriting import get_downside_stress_parameters, run_underwriting


class TestIDECORBenchmarkResolution:
    """Verify neighborhood resolution and benchmark lookup against official OMI Córdoba values."""

    def test_neighborhood_matching(self):
        assert resolve_neighborhood("Nueva Cordoba, Cordoba").neighborhood == "Nueva Córdoba"
        assert resolve_neighborhood("B° General Paz").neighborhood == "General Paz"
        assert resolve_neighborhood("Güemes").neighborhood == "Güemes"
        assert resolve_neighborhood("Cerro de las Rosas").neighborhood == "Cerro de las Rosas"
        assert resolve_neighborhood("Alberdi").neighborhood == "Alberdi / Alto Alberdi"
        assert resolve_neighborhood("Centro").neighborhood == "Centro"
        assert resolve_neighborhood("Desconocido").neighborhood == "Córdoba Capital (Promedio General)"


class TestMarketValuationAuditor:
    """Verify market pricing audit against IDECOR percentiles."""

    def test_realistic_deal_in_nueva_cordoba(self):
        opp = Opportunity(
            title="Departamento 2D Nueva Córdoba",
            location="Nueva Córdoba, Córdoba",
            strategy=StrategyType.RENOVATE_AND_SELL,
            asking_price=90000.0,
            projected_purchase_price=85000.0,
            estimated_capex=15000.0,
            holding_period_months=6,
            projected_exit_value=120000.0,
            usable_area_m2=70.0,  # purchase = 1214.29/m2, exit = 1714.29/m2
        )
        audit = audit_property_valuation(opp)

        assert audit.neighborhood == "Nueva Córdoba"
        assert audit.is_exit_realistic is True
        assert audit.is_below_market_entry is True  # 1214 < 1400 (P25)
        assert audit.purchase_price_per_m2 == pytest.approx(1214.29, abs=0.1)
        assert audit.exit_price_per_m2 == pytest.approx(1714.29, abs=0.1)
        assert len(audit.warnings) == 0

    def test_overpriced_exit_triggers_warning(self):
        opp = Opportunity(
            title="Depto Sobrevaluado",
            location="Nueva Córdoba",
            strategy=StrategyType.RENOVATE_AND_SELL,
            asking_price=100000.0,
            projected_purchase_price=95000.0,
            estimated_capex=10000.0,
            holding_period_months=6,
            projected_exit_value=180000.0,
            usable_area_m2=60.0,  # exit = 3000/m2 (P75 is 2100)
        )
        audit = audit_property_valuation(opp)

        assert audit.is_exit_realistic is False
        assert any("Alerta de salida" in w for w in audit.warnings)
        assert audit.exit_deviation_pct is not None
        assert audit.exit_deviation_pct > 50.0  # >50% over median

    def test_missing_usable_area_graceful_handling(self):
        opp = Opportunity(
            title="Sin m2",
            location="General Paz",
            strategy=StrategyType.BUY_AND_HOLD,
            asking_price=60000.0,
            projected_purchase_price=55000.0,
            holding_period_months=12,
            projected_exit_value=70000.0,
            usable_area_m2=None,
        )
        audit = audit_property_valuation(opp)

        assert audit.usable_area_m2 is None
        assert audit.is_exit_realistic is True
        assert any("no especifica m2" in w for w in audit.warnings)


class TestCommitteeIntegrationWithMarketAudit:
    """Verify RiskAgent and LangGraph committee react to IDECOR valuation audits."""

    def test_risk_agent_penalizes_overpriced_exit(self):
        opp = Opportunity(
            title="Depto Inflado",
            location="General Paz, Córdoba",
            strategy=StrategyType.RENOVATE_AND_SELL,
            asking_price=90000.0,
            projected_purchase_price=80000.0,
            estimated_capex=10000.0,
            holding_period_months=6,
            projected_exit_value=150000.0,
            usable_area_m2=50.0,  # exit = 3000/m2 vs P75 = 1750/m2
        )
        uw = UnderwritingAgent().evaluate(opp)
        risk_eval = RiskAgent().evaluate(opp, uw, risk_tolerance=RiskTolerance.MEDIUM)

        assert risk_eval.market_audit is not None
        assert risk_eval.market_audit.is_exit_realistic is False
        assert risk_eval.is_acceptable_risk is False
        assert any("Salida sobrevaluada vs IDECOR" in f for f in risk_eval.risk_flags)

    def test_langgraph_committee_incorporates_market_audit(self):
        opp = Opportunity(
            title="Piso en Nueva Córdoba",
            location="Nueva Córdoba, Córdoba",
            strategy=StrategyType.RENOVATE_AND_SELL,
            asking_price=100000.0,
            projected_purchase_price=90000.0,
            estimated_capex=20000.0,
            holding_period_months=8,
            projected_exit_value=145000.0,
            usable_area_m2=85.0,  # Exit: ~1705/m2 (Mediana: 1750/m2)
        )
        mandate = InvestorMandate(
            investor_name="Family Office Córdoba",
            capital_available=200000.0,
            target_irr=0.15,
            investment_horizon_months=12,
            geography=["Cordoba"],
            strategies=[StrategyType.RENOVATE_AND_SELL],
            risk_tolerance=RiskTolerance.MEDIUM,
        )

        state = run_langgraph_committee(opp, mandate)

        assert state["market_audit"] is not None
        assert state["market_audit"]["neighborhood"] == "Nueva Córdoba"
        assert state["market_audit"]["is_exit_realistic"] is True
        assert any("IDECOR" in t for t in state["audit_trail"])
        assert "Auditoría IDECOR" in (state["risk_critique"] or "")


class TestDynamicDownsideStressMatrix:
    """Verify stress factors across various investment strategies."""

    def test_stress_parameters_matrix(self):
        renovate_stress = get_downside_stress_parameters(StrategyType.RENOVATE_AND_SELL)
        assert renovate_stress["capex_multiplier"] == 1.25
        assert renovate_stress["duration_delta_months"] == 4.0
        assert renovate_stress["exit_price_multiplier"] == 0.88

        rental_stress = get_downside_stress_parameters(StrategyType.BUY_AND_HOLD)
        assert rental_stress["capex_multiplier"] == 1.10
        assert rental_stress["vacancy_months"] == 3.0
        assert rental_stress["rent_multiplier"] == 0.85

        pre_con_stress = get_downside_stress_parameters(StrategyType.PRE_CONSTRUCTION)
        assert pre_con_stress["capex_multiplier"] == 1.00
        assert pre_con_stress["duration_delta_months"] == 8.0

        distressed_stress = get_downside_stress_parameters(StrategyType.DISTRESSED)
        assert distressed_stress["capex_multiplier"] == 1.35
        assert distressed_stress["duration_delta_months"] == 12.0
