# Architecture Annex: Local Market Validation (IDECOR/OMI) & Dynamic Downside

## 1. Context & Business Rationale
This annex extends Sections 12 (*Escenarios*), 14 (*Risk Engine*), and 16.5 (*Market Data Agent*) of [REAL_ESTATE_CAPITAL_OS_MASTER_v0.1.md](../REAL_ESTATE_CAPITAL_OS_MASTER_v0.1.md).

Real estate risk and exit valuations cannot be treated with static, one-size-fits-all assumptions:
1. **Dynamic Downside:** A rental property (*Buy & Hold*) carries vacancy and tenant default risk, whereas a renovation (*Renovate & Sell*) carries execution cost overruns and liquidity delays. The Downside scenario must reflect the operational reality of each strategy.
2. **Local Market Benchmarks (IDECOR / OMI Córdoba):** The province of Córdoba features the *Observatorio del Mercado Inmobiliario (OMI)* managed by IDECOR. Rather than computing custom spatial econometric models from scratch, the system consumes official neighborhood property values per square meter (USD/m²) to audit whether acquisition prices and exit valuations reflect real market bounds.

---

## 2. Dynamic Downside Stress Matrix

| Strategy (`StrategyType`) | Capex Stress | Duration Stress | Exit Valuation Stress | Operating / Rental Stress |
| :--- | :--- | :--- | :--- | :--- |
| **`renovate_and_sell`** | +25% capex | +4 months | -12% exit price | N/A |
| **`buy_and_hold`** | +10% capex | +0 months | -10% exit price | 3 months vacancy, -15% real rent |
| **`pre_construction`** | +0% (fixed) | +8 months delivery delay | -10% exit price | N/A |
| **`distressed`** | +35% capex | +12 months legal delay | -15% exit price | N/A |
| **`development`** | +25% capex | +6 months construction delay | -15% exit price | N/A |

---

## 3. IDECOR / OMI Market Benchmark Tool

### Canonical Benchmarks for Córdoba Capital (USD/m² Built / Finished)
* **Nueva Córdoba:** USD 1,400 – 2,100 / m² (Median: USD 1,750 / m²)
* **General Paz:** USD 1,200 – 1,750 / m² (Median: USD 1,450 / m²)
* **Güemes:** USD 1,150 – 1,650 / m² (Median: USD 1,380 / m²)
* **Cerro de las Rosas:** USD 1,300 – 2,200 / m² (Median: USD 1,700 / m²)
* **Alberdi / Alto Alberdi:** USD 850 – 1,250 / m² (Median: USD 1,050 / m²)
* **Centro:** USD 900 – 1,350 / m² (Median: USD 1,100 / m²)

### Audit Logic in the Committee
1. Compute $\text{Projected Exit USD/m²} = \frac{\text{Projected Exit Value}}{\text{usable\_area\_m2}}$.
2. If $\text{Projected Exit USD/m²} > \text{P75 Benchmark}$, trigger a warning for inflated exit assumption.
3. If $\text{Acquisition USD/m²} < \text{P25 Benchmark}$, confirm genuine below-market entry (distressed / negotiation upside).
