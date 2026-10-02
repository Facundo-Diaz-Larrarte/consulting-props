"""Specialized Investment Committee Agents for Real Estate Capital OS.

Implements Sections 16.7, 16.8, 16.9, 16.12 of Master Project Document:
- Underwriting Agent (Project Evaluation)
- Risk Agent (Independent Risk Stress-Testing)
- Matching Agent (Investor Mandate Compatibility)
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from core.schemas import (
    InvestorMandate,
    Opportunity,
    RiskTolerance,
    UnderwritingModel,
)
from core.underwriting import run_underwriting


class UnderwritingEvaluation(BaseModel):
    """Output report from the Underwriting Agent."""
    opportunity_id: str
    irr_annualized: float
    moic: float
    npv: float
    net_profit: float
    underwriting_model: UnderwritingModel


class RiskEvaluation(BaseModel):
    """Output report from the Risk Agent."""
    opportunity_id: str
    risk_score: float = Field(..., ge=0, le=100, description="100 = minimal risk, 0 = critical risk")
    downside_irr: float
    downside_profit: float
    capex_intensity_pct: float
    risk_flags: List[str] = Field(default_factory=list)
    is_acceptable_risk: bool


class MatchEvaluation(BaseModel):
    """Output report from the Mandate Matching Agent."""
    opportunity_id: str
    mandate_id: str
    is_hard_match: bool
    capital_fit: bool
    geography_fit: bool
    strategy_fit: bool
    return_fit: bool
    fit_score: float = Field(..., ge=0, le=100)
    reasons: List[str] = Field(default_factory=list)


class UnderwritingAgent:
    """Agent 16.8: Project Evaluation Agent. Runs deterministic DCF and sensitivity analysis."""

    def evaluate(self, opportunity: Opportunity, discount_rate_annual: float = 0.10) -> UnderwritingEvaluation:
        uw_model = run_underwriting(opportunity, discount_rate_annual=discount_rate_annual)
        return UnderwritingEvaluation(
            opportunity_id=opportunity.id,
            irr_annualized=uw_model.irr_annualized,
            moic=uw_model.moic,
            npv=uw_model.npv,
            net_profit=uw_model.net_profit,
            underwriting_model=uw_model,
        )


class RiskAgent:
    """Agent 16.9: Independent Risk Agent. Stress-tests deal assumptions without commercial bias."""

    def evaluate(self, opportunity: Opportunity, uw: UnderwritingEvaluation, risk_tolerance: RiskTolerance = RiskTolerance.MEDIUM) -> RiskEvaluation:
        flags = []
        score = 100.0

        downside = uw.underwriting_model.scenarios.get("downside")
        downside_irr = downside.irr_annualized if downside else 0.0
        downside_profit = downside.net_profit if downside else 0.0

        # 1. Downside profitability
        if downside_profit < 0:
            flags.append("CRITICAL: Escenario adverso destruye capital (utilidad negativa en Downside).")
            score -= 35.0
        elif downside_irr < 0.05:
            flags.append("MODERATE: Escenario adverso rinde por debajo de tasa libre de riesgo (<5% anual).")
            score -= 15.0

        # 2. Capex intensity (capex / purchase price)
        capex_ratio = opportunity.estimated_capex / opportunity.projected_purchase_price if opportunity.projected_purchase_price > 0 else 0
        if capex_ratio > 0.35:
            flags.append(f"HIGH: Alta intensidad de obra/reforma ({capex_ratio:.1%} del precio de compra).")
            score -= 20.0
        elif capex_ratio > 0.20:
            flags.append(f"MODERATE: Intensidad media de reforma ({capex_ratio:.1%} del precio).")
            score -= 10.0

        # 3. Holding duration / liquidity risk
        if opportunity.holding_period_months > 24:
            flags.append("HIGH: Plazo de recupero superior a 24 meses (riesgo elevado de iliquidez).")
            score -= 20.0
        elif opportunity.holding_period_months > 14:
            flags.append(f"MODERATE: Plazo extendido ({opportunity.holding_period_months} meses).")
            score -= 10.0

        score = max(0.0, min(100.0, score))

        # Acceptability based on investor risk tolerance
        min_acceptable_score = {
            RiskTolerance.LOW: 80.0,
            RiskTolerance.MEDIUM: 60.0,
            RiskTolerance.HIGH: 45.0,
        }.get(risk_tolerance, 60.0)

        is_acceptable = score >= min_acceptable_score and downside_profit >= 0

        return RiskEvaluation(
            opportunity_id=opportunity.id,
            risk_score=score,
            downside_irr=downside_irr,
            downside_profit=downside_profit,
            capex_intensity_pct=capex_ratio,
            risk_flags=flags,
            is_acceptable_risk=is_acceptable,
        )


class MatchingAgent:
    """Agent 16.12: Matching Agent. Evaluates alignment between an Opportunity and an InvestorMandate."""

    def evaluate(self, opportunity: Opportunity, uw: UnderwritingEvaluation, mandate: InvestorMandate) -> MatchEvaluation:
        reasons = []
        fit_points = 0.0

        # 1. Capital sizing
        capital_required = opportunity.total_capital_required
        capital_fit = capital_required <= mandate.capital_available
        if capital_fit:
            fit_points += 25.0
            reasons.append(f"Capital requerido (${capital_required:,.0f}) encaja dentro del disponible (${mandate.capital_available:,.0f}).")
        else:
            reasons.append(f"Capital requerido (${capital_required:,.0f}) SUPERA el capital disponible (${mandate.capital_available:,.0f}).")

        # 2. Geography
        geography_fit = any(geo.lower() in opportunity.location.lower() for geo in mandate.geography)
        if geography_fit:
            fit_points += 25.0
            reasons.append(f"Ubicación ({opportunity.location}) coincide con mandato ({', '.join(mandate.geography)}).")
        else:
            reasons.append(f"Ubicación ({opportunity.location}) fuera de geografía objetivo ({', '.join(mandate.geography)}).")

        # 3. Strategy
        strategy_fit = opportunity.strategy in mandate.strategies
        if strategy_fit:
            fit_points += 25.0
            reasons.append(f"Estrategia ({opportunity.strategy.value}) autorizada en mandato.")
        else:
            reasons.append(f"Estrategia ({opportunity.strategy.value}) NO contemplada en mandato.")

        # 4. Return hurdle
        return_fit = uw.irr_annualized >= mandate.target_irr
        if return_fit:
            fit_points += 25.0
            reasons.append(f"TIR proyectada ({uw.irr_annualized:.1%}) supera umbral objetivo ({mandate.target_irr:.1%}).")
        else:
            reasons.append(f"TIR proyectada ({uw.irr_annualized:.1%}) por debajo del objetivo ({mandate.target_irr:.1%}).")

        is_hard_match = capital_fit and geography_fit and strategy_fit and return_fit

        return MatchEvaluation(
            opportunity_id=opportunity.id,
            mandate_id=mandate.id,
            is_hard_match=is_hard_match,
            capital_fit=capital_fit,
            geography_fit=geography_fit,
            strategy_fit=strategy_fit,
            return_fit=return_fit,
            fit_score=fit_points,
            reasons=reasons,
        )
