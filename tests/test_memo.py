"""Tests for Investment Memo generation."""

from core.schemas import Opportunity, StrategyType
from core.underwriting import run_underwriting
from core.memo import generate_investment_memo


def test_generate_investment_memo_structure():
    opp = Opportunity(
        title="Casa Barrio Jardin",
        location="Barrio Jardin, Cordoba",
        strategy=StrategyType.RENOVATE_AND_SELL,
        asking_price=150000,
        projected_purchase_price=135000,
        estimated_capex=25000,
        holding_period_months=12,
        projected_exit_value=210000,
    )
    uw = run_underwriting(opp)
    memo = generate_investment_memo(opp, uw)

    assert memo.opportunity_id == opp.id
    assert "INVESTMENT MEMORANDUM: CASA BARRIO JARDIN" in memo.markdown_content
    assert "Executive Overview" in memo.markdown_content
    assert "Scenario Analysis" in memo.markdown_content
    assert memo.capital_required == opp.total_capital_required
    assert memo.target_irr == uw.irr_annualized
    assert len(memo.key_risks) >= 3
