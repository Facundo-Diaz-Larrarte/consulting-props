"""Investment Committee Coordinator for Real Estate Capital OS.

Implements Section 17 (Investment Committee Consensus & Decision Protocol):
Synthesizes reports from Underwriting, Risk, and Matching Agents to deliver
a binding institutional verdict: APPROVED, REJECTED, or COUNTER_OFFER.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from core.agents.committee import (
    MatchEvaluation,
    MatchingAgent,
    RiskAgent,
    RiskEvaluation,
    UnderwritingAgent,
    UnderwritingEvaluation,
)
from core.memo import generate_investment_memo
from core.schemas import DealStage, InvestmentMemo, InvestorMandate, Opportunity
from core.underwriting import run_underwriting


class CommitteeVerdictType(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    COUNTER_OFFER = "counter_offer"


class CommitteeVerdict(BaseModel):
    """The collective decision of the Investment Committee."""
    opportunity_id: str
    mandate_id: str
    verdict: CommitteeVerdictType
    rationale: str
    max_recommended_bid: Optional[float] = None
    underwriting: UnderwritingEvaluation
    risk: RiskEvaluation
    match: MatchEvaluation
    memo: Optional[InvestmentMemo] = None


class InvestmentCommitteeCoordinator:
    """Coordinator that orchestrates the specialized agents and derives a consensus verdict."""

    def __init__(self):
        self.underwriter = UnderwritingAgent()
        self.risk_officer = RiskAgent()
        self.matcher = MatchingAgent()

    def evaluate_deal(
        self,
        opportunity: Opportunity,
        mandate: InvestorMandate,
        discount_rate_annual: float = 0.10,
    ) -> CommitteeVerdict:
        """Run the full committee pipeline and synthesize the consensus verdict."""

        # 1. Quantitative Underwriting
        uw_eval = self.underwriter.evaluate(opportunity, discount_rate_annual=discount_rate_annual)

        # 2. Risk Stress-Testing
        risk_eval = self.risk_officer.evaluate(
            opportunity,
            uw_eval,
            risk_tolerance=mandate.risk_tolerance,
        )

        # 3. Mandate Matching
        match_eval = self.matcher.evaluate(opportunity, uw_eval, mandate)

        # 4. Consensus & Decision Logic
        # Case A: Fatal mismatch or catastrophic risk -> REJECTED
        if not match_eval.capital_fit or not match_eval.geography_fit or not match_eval.strategy_fit or not match_eval.horizon_fit:
            verdict = CommitteeVerdictType.REJECTED
            rationale = "Rechazado por incompatibilidad estructural con el mandato (monto, geografía, estrategia o plazo/horizonte)."
            memo = None
            max_bid = None

        elif uw_eval.net_profit <= 0:
            verdict = CommitteeVerdictType.REJECTED
            rationale = "Rechazado por inviabilidad económica: la inversión no genera rentabilidad neta positiva en escenario base."
            memo = None
            max_bid = None

        # Case B: Approved (Hard match and risk acceptable)
        elif match_eval.is_hard_match and risk_eval.is_acceptable_risk:
            verdict = CommitteeVerdictType.APPROVED
            opportunity.status = DealStage.APPROVED
            rationale = (
                f"Aprobado por el Comité. TIR base ({uw_eval.irr_annualized:.1%}) supera el objetivo ({mandate.target_irr:.1%}) "
                f"con score de riesgo aceptable ({risk_eval.risk_score:.0f}/100)."
            )
            memo = generate_investment_memo(
                opportunity=opportunity,
                underwriting=uw_eval.underwriting_model,
                thesis=f"Oportunidad calificada en {opportunity.location} que satisface el mandato de {mandate.investor_name}.",
                key_risks=risk_eval.risk_flags or ["Riesgo ordinario de mercado y plazo."],
            )
            max_bid = opportunity.projected_purchase_price

        # Case C: Counter-Offer (Good asset/location/strategy, but price too high for target IRR or risk margin)
        else:
            verdict = CommitteeVerdictType.COUNTER_OFFER
            max_bid = self._calculate_max_bid(opportunity, mandate.target_irr, discount_rate_annual)
            rationale = (
                f"Contraoferta recomendada. Al precio proyectado actual (${opportunity.projected_purchase_price:,.0f}), "
                f"el retorno ({uw_eval.irr_annualized:.1%}) o el perfil de riesgo no alcanzan el objetivo. "
                f"Precio máximo de compra sugerido: ${max_bid:,.0f} USD."
            )
            # Generate memo adjusted to the counter-offer
            adjusted_opp = opportunity.model_copy(update={"projected_purchase_price": max_bid, "status": DealStage.NEGOTIATION})
            adjusted_uw = run_underwriting(adjusted_opp, discount_rate_annual=discount_rate_annual)
            memo = generate_investment_memo(
                opportunity=adjusted_opp,
                underwriting=adjusted_uw,
                thesis=f"Oportunidad viable condicionada a contraoferta agresiva de entrada a ${max_bid:,.0f} USD.",
                key_risks=risk_eval.risk_flags,
            )

        return CommitteeVerdict(
            opportunity_id=opportunity.id,
            mandate_id=mandate.id,
            verdict=verdict,
            rationale=rationale,
            max_recommended_bid=max_bid,
            underwriting=uw_eval,
            risk=risk_eval,
            match=match_eval,
            memo=memo,
        )

    def _calculate_max_bid(self, opportunity: Opportunity, target_irr: float, discount_rate_annual: float) -> float:
        """Binary search solver to determine the maximum purchase price that achieves target IRR."""
        low = opportunity.projected_purchase_price * 0.40
        high = opportunity.projected_purchase_price * 1.05
        best_price = low

        for _ in range(25):
            mid = (low + high) / 2.0
            test_opp = opportunity.model_copy(update={"projected_purchase_price": mid})
            test_uw = run_underwriting(test_opp, discount_rate_annual=discount_rate_annual)

            if test_uw.irr_annualized >= target_irr:
                best_price = mid
                low = mid  # Can afford a higher price
            else:
                high = mid  # Must offer less

        return round(best_price, -2)  # Round to nearest 100 USD
