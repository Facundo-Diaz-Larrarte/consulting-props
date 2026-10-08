# Feature: Real Estate Capital OS — Monetization Engine & Unit Economics (Sections 21 & 22)

## Status
- **State**: In Progress
- **Feature Identity**: `re-capital-os-monetization-and-unit-economics`
- **Delivery Strategy**: `ask-on-risk`
- **TDD Mode**: Disabled (verification via automated functional test suites with pytest)
- **Line Forecast**: ~420 lines

---

## 1. Context & Objective
Implement the Platform Monetization and Unit Economics Engine specified in Sections 21 (*Modelo de monetización*) and 22 (*Economía del negocio*) of the Master Document.

Institutional real estate syndication requires transparently decoupling:
1. **Asset-Level Performance (Gross):** Real estate project IRR, NPV, and MOIC.
2. **Platform Monetization (Revenue & Take Rate):** Origination, Structuring, Success, and Performance Fees (Carry with Hurdle Rate Waterfall).
3. **Investor-Level Performance (Net):** Net cashflow schedule, Net IRR, and Net MOIC after platform fees.
4. **Platform Unit Economics:** GMV, Effective Take Rate (target 5–10%), Direct Costs, and Contribution Margin.

---

## 2. Tasks & Progress

- [x] **TASK-01**: Document architecture annex in `docs/MONETIZATION_AND_UNIT_ECONOMICS.md` and initialize ODD tracking
  - Route: Direct inline
  - Checks: Formalizes fee schedule, hurdle rate waterfall logic, and unit economics formulas.
  - Evidence: Documented in docs/MONETIZATION_AND_UNIT_ECONOMICS.md.

- [ ] **TASK-02**: Implement `FeeSchedule` and Hurdle Rate Waterfall distribution in `core/monetization.py`
  - Route: Direct inline
  - Checks: Calculates origination fee, structuring fee, success fee, and carry over hurdle rate.
  - Evidence: Commit pending.

- [ ] **TASK-03**: Implement Net Investor Return and Platform Economics calculations
  - Route: Direct inline
  - Checks: Net cashflows, Net IRR/MOIC/NPV, GMV, effective take rate, and contribution margin.
  - Evidence: Commit pending.

- [ ] **TASK-04**: Integrate monetization breakdown into Investment Memo and verify with unit tests in `tests/test_monetization.py`
  - Route: Direct inline
  - Checks: All unit tests pass verifying fee calculation, net metrics, and memo generation.
  - Evidence: Commit pending.

---

## 3. Verification & Evidence
- Tests: `pytest`
- Syntax: `python -m py_compile`
