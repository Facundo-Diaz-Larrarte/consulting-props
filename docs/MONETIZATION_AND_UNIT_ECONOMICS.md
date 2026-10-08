# Architecture Annex: Platform Monetization & Unit Economics

## 1. Context & Business Rationale
This annex operationalizes Sections 21 (*Modelo de monetización*) and 22 (*Economía del negocio*) of [REAL_ESTATE_CAPITAL_OS_MASTER_v0.1.md](../REAL_ESTATE_CAPITAL_OS_MASTER_v0.1.md).

In institutional real estate private equity, asset profitability must be distinguished from investor net yield and platform revenue:
1. **Asset Gross Metrics:** Return generated strictly by property acquisition, renovation, rental, and exit.
2. **Platform Monetization:** Fees earned by Real Estate Capital OS for origination, structuring, execution, and performance.
3. **Investor Net Metrics:** True return received by the LP/investor after all platform fees and carry.
4. **Platform Unit Economics:** Gross Merchandise Value (GMV), Revenue, Effective Take Rate, and Contribution Margin.

---

## 2. Fee Structure Specification (Section 21)

| Fee Type | Timing | Benchmark Base | Default Rate | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Origination Fee** | Month 0 (Entry) | Projected Purchase Price | 1.50% | Fee for sourcing and qualifying proprietary off-market inventory. |
| **Structuring Fee** | Month 0 (Entry) | Total Capital Required | 1.00% | Fee for underwriting, legal diligence, and syndicate architecture. |
| **Success Fee** | Final Month (Exit) | Projected Exit Value | 1.50% | Fee upon successful asset divestment and capital liquidation. |
| **Performance Fee (Carry)** | Final Month (Exit) | Profit exceeding Hurdle Rate | 20.00% | Incentive carry aligned with investor upside above preferred return. |

### Performance Fee Waterfall (Hurdle Rate)
- **Preferred Return (Hurdle Rate):** 12.0% Annualized IRR.
- If Net Annualized IRR to investor $\le 12.0\%$: Carry is $0 (100% of profit to investor).
- If Net Annualized IRR $> 12.0\%$: Platform receives $20\%$ of the profit above the hurdle threshold.

---

## 3. Unit Economics & Take Rate (Section 22)

### Formulas
$$\text{GMV} = \text{Projected Purchase Price} + \text{Estimated Capex} + \text{Projected Exit Value}$$

$$\text{Platform Revenue} = \text{Origination Fee} + \text{Structuring Fee} + \text{Success Fee} + \text{Performance Fee}$$

$$\text{Effective Take Rate} = \frac{\text{Platform Revenue}}{\text{GMV}}$$
*(Target range defined in Section 22: 5.0% – 10.0%)*

$$\text{Contribution Margin} = \text{Platform Revenue} - \text{Direct Transaction Costs}$$
$$\text{Contribution Margin \%} = \frac{\text{Contribution Margin}}{\text{Platform Revenue}}$$
*(Direct transaction costs include notary verification, property inspection, and title search).*

---

## 4. Net Investor Metrics

The investor's cashflows reflect:
- **Month 0 Outflow:** Initial capital deployment + Upfront platform fees ($\text{Purchase} + \text{Closing Costs} + \text{Capex} + \text{Origination Fee} + \text{Structuring Fee}$).
- **Operating Months:** Net operating rental cashflows.
- **Exit Month Inflow:** Net exit proceeds $-\text{Success Fee} - \text{Performance Fee}$.
- **Calculated Yields:** $\text{Net IRR Annualized}$, $\text{Net MOIC}$, $\text{Net NPV}$.
