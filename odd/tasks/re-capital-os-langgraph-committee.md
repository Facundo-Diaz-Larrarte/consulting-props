# Feature: Real Estate Capital OS — LangGraph Multi-Agent Committee

## Status
- **State**: Completed
- **Feature Identity**: `re-capital-os-langgraph-committee`
- **Engram Mirror**: Pending (Engram tools unavailable in session)
- **Delivery Strategy**: `ask-on-risk`
- **TDD Mode**: Disabled (verification via automated functional test suites with pytest)
- **Line Forecast**: ~350 lines

---

## 1. Context & Objective
Integrate the industry-standard **LangGraph** framework to power the multi-agent Investment Committee (Sections 16 & 17 of [REAL_ESTATE_CAPITAL_OS_MASTER_v0.1.md](../../REAL_ESTATE_CAPITAL_OS_MASTER_v0.1.md)), achieving the optimal balance between high-speed execution and production-grade stateful multi-agent debate.

### Architecture
- **StateGraph**: `CommitteeState` tracking Opportunity, Mandate, Agent Deliberations, and Final Verdict.
- **Nodes**:
  - `underwriter_agent`: Evaluates DCF and return metrics via `core/underwriting.py` tools.
  - `risk_agent`: Challenges assumptions, analyzes downside capex/delay impacts.
  - `coordinator_agent`: Reaches consensus verdict and drafts the Investment Memo.
- **Conditional Edges**: Dynamic routing based on deal qualification.

---

## 2. Tasks & Progress

- [x] **TASK-01**: Implement LangGraph StateGraph in `core/agents/langgraph_committee.py`
  - Route: Direct inline
  - Checks: StateGraph compiles, connects nodes with conditional routing, and supports LLM reasoning with tool integration (Verified).
  - Evidence: Commit `cc0c049`

- [x] **TASK-02**: Implement test suite in `tests/test_langgraph_committee.py`
  - Route: Direct inline
  - Checks: Pytest verifies graph compilation, state accumulation across nodes, and correct verdict outputs (3/3 tests passed, 22 total passed).
  - Evidence: Commit `cc0c049`

- [x] **TASK-03**: Build execution simulation script in `scripts/run_langgraph_committee.py`
  - Route: Direct inline
  - Checks: Script runs end-to-end deliberation through LangGraph showing multi-agent reasoning stream (Verified with execution output).
  - Evidence: Commit `cc0c049`

---

## 3. Verification & Evidence
- Tests: `pytest`
- Execution: `scripts/run_langgraph_committee.py`
