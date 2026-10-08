# Feature: Real Estate Capital OS — Market Validation (IDECOR) & Dynamic Downside

## Status
- **State**: In Progress
- **Feature Identity**: `re-capital-os-market-validation-and-downside`
- **Engram Mirror**: Pending (Engram tools unavailable in session)
- **Delivery Strategy**: `ask-on-risk`
- **TDD Mode**: Disabled (verification via automated functional test suites with pytest)
- **Line Forecast**: ~380 lines

---

## 1. Context & Objective
Implement the local market data validation tool using official Córdoba land and property benchmarks (IDECOR / OMI), and replace generic financial downside with strategy-specific stress models (`renovate_and_sell`, `buy_and_hold`, `pre_construction`, `distressed`).

### Scope
1. Architecture Annex documentation in `docs/MARKET_VALIDATION_AND_DOWNSIDE.md`.
2. Add `usable_area_m2` to `Opportunity` in `core/schemas.py`.
3. Strategy-specific stress factors in `core/underwriting.py` (`calculate_scenario`).
4. IDECOR / OMI benchmark tool in `core/tools/idecor.py` auditing USD/m² vs neighborhood ranges.
5. Integration into the LangGraph Investment Committee (`risk_officer` & `underwriter` nodes).
6. Comprehensive unit test suite in `tests/test_market_validation.py`.

---

## 2. Tasks & Progress

- [x] **TASK-01**: Document architecture annex in `docs/MARKET_VALIDATION_AND_DOWNSIDE.md`
  - Route: Direct inline
  - Checks: Documents IDECOR data model and strategy-specific downside stress matrices.
  - Evidence: Completed in docs/MARKET_VALIDATION_AND_DOWNSIDE.md.

- [x] **TASK-02**: Implement strategy-specific dynamic downside in `core/underwriting.py` and update `core/schemas.py`
  - Route: Direct inline
  - Checks: Opportunity supports `usable_area_m2`. Downside scenario adapts capex, duration, vacancy, and exit based on `StrategyType`.
  - Evidence: Verified with 24 passing pytest unit tests.

- [ ] **TASK-03**: Create IDECOR Market Benchmark Tool in `core/tools/idecor.py`
  - Route: Direct inline
  - Checks: Audits target price per m² against official Córdoba neighborhood ranges (Nueva Córdoba, General Paz, Güemes, etc.).
  - Evidence: Commit hash pending.

- [ ] **TASK-04**: Integrate market audit into LangGraph Committee and verify with unit tests in `tests/test_market_validation.py`
  - Route: Direct inline
  - Checks: All unit tests pass verifying dynamic downside and IDECOR benchmark checks.
  - Evidence: Commit hash pending.

---

## 3. Verification & Evidence
- Tests: `pytest`
- Linters/syntax: `python -m py_compile`
