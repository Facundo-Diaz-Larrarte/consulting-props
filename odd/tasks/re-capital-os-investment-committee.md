# Feature: Real Estate Capital OS — Investment Committee & Multi-Agent Consensus

## Status
- **State**: Completed
- **Feature Identity**: `re-capital-os-investment-committee`
- **Engram Mirror**: Pending (Engram tools unavailable in session)
- **Delivery Strategy**: `ask-on-risk`
- **TDD Mode**: Disabled (verification via automated functional test suites with pytest)
- **Line Forecast**: ~400 lines

---

## 1. Context & Objective
Implement the multi-agent Investment Committee pipeline as specified in Sections 16 and 17 of [REAL_ESTATE_CAPITAL_OS_MASTER_v0.1.md](../../REAL_ESTATE_CAPITAL_OS_MASTER_v0.1.md), leveraging the specialized debate and consensus topology proven in `ai-hedge-fund`.

### Pipeline Architecture (Section 17)
`Normalization → Underwriting Agent → Risk Agent → Mandate Matching Agent → Committee Coordinator (Verdict & Memo)`

### Scope
1. Specialized Agent Roles in `core/agents/committee.py`:
   - `UnderwritingAgent`: Evaluates raw financials using `core.underwriting`.
   - `RiskAgent`: Stress-tests construction delays, liquidity, and downside margins.
   - `MatchingAgent`: Tests asset fit against `InvestorMandate` criteria.
2. Committee Coordinator in `core/agents/coordinator.py`:
   - Synthesizes findings, computes maximum allowable purchase price for target IRR, and renders verdicts: `APPROVED`, `REJECTED`, or `COUNTER_OFFER`.
3. Unit Test Suite in `tests/test_committee.py`.
4. Committee Simulation in `scripts/run_committee_simulation.py` ranking 3 competing opportunities in Córdoba.

---

## 2. Tasks & Progress

- [x] **TASK-01**: Implement specialized committee role agents in `core/agents/committee.py`
  - Route: Direct inline
  - Checks: Agents instantiate, evaluate opportunities against mandates, and return structured evaluations (Verified).
  - Evidence: Commit `dd69259`

- [x] **TASK-02**: Implement `InvestmentCommitteeCoordinator` in `core/agents/coordinator.py`
  - Route: Direct inline
  - Checks: Consensus engine renders verdicts (`APPROVED`, `REJECTED`, `COUNTER_OFFER`) and attaches risk-adjusted recommendations (Verified).
  - Evidence: Commit `dd69259`

- [x] **TASK-03**: Create unit test suite in `tests/test_committee.py`
  - Route: Direct inline
  - Checks: Pytest verifies approved deals, rejected deals (high risk / low IRR), and price recalculation for counter-offers (4/4 tests passed).
  - Evidence: Commit `dd69259`

- [x] **TASK-04**: Build multi-deal simulation runner in `scripts/run_committee_simulation.py`
  - Route: Direct inline
  - Checks: Script runs 3 Córdoba deals through the committee and ranks them by risk-adjusted return (Verified with execution output).
  - Evidence: Commit `dd69259`

---

## 3. Verification & Evidence
- Tests: `pytest`
- End-to-end check: Execution of `scripts/run_committee_simulation.py` with 3 deals.
