# Feature: Real Estate Capital OS — MVP Core & Financial Engine

## Status
- **State**: In Progress
- **Feature Identity**: `re-capital-os-mvp`
- **Engram Mirror**: Pending (Engram tools unavailable in session)
- **Delivery Strategy**: `ask-on-risk`
- **TDD Mode**: Disabled (verification via automated functional test suites with pytest)
- **Line Forecast**: ~450 lines (authored behavior + tests)

---

## 1. Context & Objective
Implement the foundational domain models, deterministic financial underwriting engine, memo generator, and initial extraction agent as prescribed by [REAL_ESTATE_CAPITAL_OS_MASTER_v0.1.md](../../REAL_ESTATE_CAPITAL_OS_MASTER_v0.1.md) (Sections 11–16, 37, 43–45).

### Problem
Real estate deals are evaluated manually, informally, and without standardized economic underwriting. Fragmented inputs from brokers and sellers must be normalized into structured opportunities, evaluated with strict financial mathematics (IRR, NPV, MOIC, sensitivity), and matched against investor mandates.

### Scope
- The 5 canonical domain objects: `InvestorMandate`, `Opportunity`, `UnderwritingModel`, `InvestmentMemo`, `DealPipeline`.
- Deterministic Python financial engine calculating monthly cash flows, annualized IRR, NPV, MOIC, and sensitivity matrix.
- Structured Investment Memo generator.
- AI Ingestion module extracting typed opportunities from unstructured text / broker sheets.
- End-to-end pilot script validating a full deal cycle for Córdoba.

### Constraints & Invariants
- Deterministic mathematics: Never delegate financial arithmetic (IRR/NPV) to LLMs.
- Strict data typing with Pydantic.
- Zero premature bloat: No blockchain, tokenization, or complex multi-tier microservices at this stage.

---

## 2. Tasks & Progress

- [ ] **TASK-01**: Define canonical Pydantic domain models in `core/schemas.py`
  - Route: Direct inline
  - Checks: Models load cleanly, validate valid payloads, reject invalid types.
  - Evidence: Commit hash pending.

- [ ] **TASK-02**: Implement deterministic Financial Underwriting Engine in `core/underwriting.py` and unit tests in `tests/test_underwriting.py`
  - Route: Delegated direct (2 non-trivial files: implementation + tests)
  - Checks: Pytest suite passes verifying IRR, NPV, MOIC, cashflows, and sensitivity calculations.
  - Evidence: Commit hash pending.

- [ ] **TASK-03**: Build Investment Memo generator in `core/memo.py`
  - Route: Direct inline
  - Checks: Generates clean, institutional Markdown memos conforming to Section 15 of master doc.
  - Evidence: Commit hash pending.

- [ ] **TASK-04**: Build AI Ingestion / Extraction Agent in `core/agents/ingestion.py`
  - Route: Direct inline
  - Checks: Converts raw property text/fichas into validated `Opportunity` objects.
  - Evidence: Commit hash pending.

- [ ] **TASK-05**: End-to-end validation script with a realistic Córdoba pilot deal in `scripts/run_pilot_deal.py`
  - Route: Direct inline
  - Checks: Script executes end-to-end: Mandate + Opportunity -> Underwriting -> Memo -> Pipeline status check.
  - Evidence: Commit hash pending.

---

## 3. Verification & Evidence
- Tests: `pytest`
- Linters/syntax: `python -m py_compile`
- Acceptance criteria: 100% test pass on financial math, end-to-end pilot script runs cleanly producing an Investment Memo.
