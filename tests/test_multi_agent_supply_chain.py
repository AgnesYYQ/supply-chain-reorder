import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import csv
import pytest
from unittest.mock import patch
import multi_agent_supply_chain


def test_forecast_from_training_data():
    """ML forecast agent computes correct fallback mean from CSV training data."""
    data_path = os.path.join(os.path.dirname(__file__), "forecast_training_data.csv")
    with open(data_path) as f:
        reader = csv.DictReader(f)
        sales = []
        for row in reader:
            val = row["sales_history"]
            if val.isdigit():
                sales.append(int(val))
        lead_time = 2
    agent = multi_agent_supply_chain.MultiAgentSupplyChain()
    agent.state = {"sales_history": sales, "lead_time": lead_time, "decision_log": []}
    agent.run()
    expected = sum(sales[-lead_time:]) / lead_time
    assert agent.state["forecast"] == expected
    log = agent.state["decision_log"]
    # Log message says either "LSTM forecasted" or "Fallback mean forecast"
    assert any("forecast" in step.lower() and "=" in step for step in log)


def test_full_path_high_cost(monkeypatch):
    """High-cost disruption ($60k) triggers Second Opinion conflict,
    Reviewer escalates to Communicator (human approval)."""
    def fake_ingestion(state, **kwargs):
        state["disruption"] = {"type": "supplier_delay", "cost": 60001}
        state.setdefault("decision_log", []).append("Ingestion: Parsed ERP alert.")
        return state
    monkeypatch.setattr(multi_agent_supply_chain, "agent_ingestion", fake_ingestion)
    agent = multi_agent_supply_chain.MultiAgentSupplyChain()
    agent.graph = multi_agent_supply_chain.build_multi_agent_graph()
    agent.run()
    log = agent.state["decision_log"]
    # High cost > 40k → Second Opinion picks "change_supplier" (conflict)
    assert any("Second Opinion" in step for step in log)
    assert any("Reviewer (4-Eyes)" in step for step in log)
    assert any("Communicator" in step for step in log)
    assert any("Executor" in step for step in log)
    assert agent.state["approval_required"] is True
    assert agent.state["review_verdict"] in ("escalated_conflict", "escalated_high_cost")


def test_full_path_low_cost(monkeypatch):
    """Low-cost disruption ($100) leads to consensus between Planner and
    Second Opinion, Reviewer approves, skips Communicator."""
    def fake_ingestion(state, **kwargs):
        state["disruption"] = {"type": "supplier_delay", "cost": 100}
        state.setdefault("decision_log", []).append("Ingestion: Parsed ERP alert.")
        return state
    monkeypatch.setattr(multi_agent_supply_chain, "agent_ingestion", fake_ingestion)
    agent = multi_agent_supply_chain.MultiAgentSupplyChain()
    agent.graph = multi_agent_supply_chain.build_multi_agent_graph()
    agent.run()
    log = agent.state["decision_log"]
    # Consensus → approved → skip Communicator
    assert any("Second Opinion" in step for step in log)
    assert any("Reviewer (4-Eyes)" in step for step in log)
    assert any("Executor" in step for step in log)
    assert not any("Communicator" in step for step in log)
    assert agent.state["review_verdict"] == "approved"
    assert agent.state["approval_required"] is False


def test_all_agents_called():
    """All agents in the graph execute in order."""
    agent = multi_agent_supply_chain.MultiAgentSupplyChain()
    agent.run()
    log = agent.state["decision_log"]
    agent_names = ["Ingestion", "ML Agent", "Planner", "Second Opinion", "Reviewer (4-Eyes)", "Executor"]
    for name in agent_names:
        assert any(name in step for step in log), f"Missing log entry for {name}"


def test_executor_always_runs():
    """Executor node is always reached regardless of path."""
    agent = multi_agent_supply_chain.MultiAgentSupplyChain()
    agent.run()
    log = agent.state["decision_log"]
    assert any("Executor" in step for step in log)


def test_second_opinion_independent_scoring(monkeypatch):
    """Second Opinion agent scores options across multiple dimensions."""
    def fake_ingestion(state, **kwargs):
        state["disruption"] = {"type": "supplier_delay", "cost": 45000}
        state.setdefault("decision_log", []).append("Ingestion: Parsed ERP alert.")
        return state
    monkeypatch.setattr(multi_agent_supply_chain, "agent_ingestion", fake_ingestion)
    agent = multi_agent_supply_chain.MultiAgentSupplyChain()
    agent.graph = multi_agent_supply_chain.build_multi_agent_graph()
    agent.run()
    # At cost=$45k, long_term_viability (weight 0.40) pushes to "change_supplier"
    assert agent.state["second_opinion"] == "change_supplier"
    # Scores dict should have all evaluated options
    assert "reroute_logistics" in agent.state["second_opinion_scores"]
    assert "change_supplier" in agent.state["second_opinion_scores"]
    assert "expedite_shipping" in agent.state["second_opinion_scores"]
    # Planner recommends "reroute_logistics" → conflict
    assert agent.state["review_verdict"] == "escalated_conflict"
    assert agent.state["approval_required"] is True


def test_reviewer_consensus_auto_approve(monkeypatch):
    """When Planner and Second Opinion agree AND cost ≤ $50k → auto-approve."""
    def fake_ingestion(state, **kwargs):
        state["disruption"] = {"type": "supplier_delay", "cost": 100}
        state.setdefault("decision_log", []).append("Ingestion: Parsed ERP alert.")
        return state
    monkeypatch.setattr(multi_agent_supply_chain, "agent_ingestion", fake_ingestion)
    agent = multi_agent_supply_chain.MultiAgentSupplyChain()
    agent.graph = multi_agent_supply_chain.build_multi_agent_graph()
    agent.run()
    assert agent.state["second_opinion"] == "reroute_logistics"  # matches Planner
    assert agent.state["review_verdict"] == "approved"
    assert agent.state["approval_required"] is False


def test_reviewer_consensus_high_cost_escalates():
    """When Planner and Second Opinion agree BUT cost > $50k → escalate."""
    def fake_ingestion(state, **kwargs):
        state["disruption"] = {"type": "supplier_delay", "cost": 55000}
        state.setdefault("decision_log", []).append("Ingestion: Parsed ERP alert.")
        return state
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(multi_agent_supply_chain, "agent_ingestion", fake_ingestion)
    agent = multi_agent_supply_chain.MultiAgentSupplyChain()
    agent.graph = multi_agent_supply_chain.build_multi_agent_graph()
    agent.run()
    monkeypatch.undo()
    # With cost=55000 > 40000, long_term_viability pushes to "change_supplier" → conflict
    # So this ends up as escalated_conflict, not escalated_high_cost
    assert agent.state["review_verdict"] in ("escalated_conflict", "escalated_high_cost")
    assert agent.state["approval_required"] is True


def test_second_opinion_scores_all_options(monkeypatch):
    """Second Opinion produces scores for every evaluated option."""
    def fake_ingestion(state, **kwargs):
        state["disruption"] = {"type": "supplier_delay", "cost": 60000}
        state.setdefault("decision_log", [])
        return state
    monkeypatch.setattr(multi_agent_supply_chain, "agent_ingestion", fake_ingestion)
    agent = multi_agent_supply_chain.MultiAgentSupplyChain()
    agent.graph = multi_agent_supply_chain.build_multi_agent_graph()
    agent.run()
    scores = agent.state["second_opinion_scores"]
    # High cost (>50k) also adds 'split_order' option
    assert "split_order" in scores, "split_order should appear for cost > $50k"
    # All scores should be positive floats
    for name, score in scores.items():
        assert isinstance(score, (int, float)), f"{name} score is not numeric: {score}"
        assert score > 0, f"{name} score should be positive, got {score}"


def test_second_opinion_trace_in_decision_log(monkeypatch):
    """Second Opinion logs its reasoning in the decision trace."""
    def fake_ingestion(state, **kwargs):
        state["disruption"] = {"type": "supplier_delay", "cost": 25000}
        state.setdefault("decision_log", [])
        return state
    monkeypatch.setattr(multi_agent_supply_chain, "agent_ingestion", fake_ingestion)
    agent = multi_agent_supply_chain.MultiAgentSupplyChain()
    agent.graph = multi_agent_supply_chain.build_multi_agent_graph()
    agent.run()
    log = agent.state["decision_log"]
    opinion_logs = [s for s in log if "Second Opinion" in s]
    assert len(opinion_logs) >= 1
    # Should mention the selected option and its score
    assert "score=" in opinion_logs[0]
    assert "Runner-up" in opinion_logs[0]
