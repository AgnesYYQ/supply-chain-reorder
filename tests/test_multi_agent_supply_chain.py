import csv
def test_simulation_forecast_from_training_data(tmp_path):
    # Load the training data CSV
    import os
    data_path = os.path.join(os.path.dirname(__file__), "forecast_training_data.csv")
    with open(data_path) as f:
        reader = csv.DictReader(f)
        sales = []
        for row in reader:
            val = row["sales_history"]
            if val.isdigit():
                sales.append(int(val))
        lead_time = 2  # All rows have lead_time=2
    # Inject sales_history and lead_time into state
    agent = multi_agent_supply_chain.MultiAgentSupplyChain()
    agent.state = {"sales_history": sales, "lead_time": lead_time, "decision_log": []}
    agent.run()
    # The forecast should be the mean of the last 'lead_time' sales
    expected = sum(sales[-lead_time:]) / lead_time
    assert agent.state["forecast"] == expected
    log = agent.state["decision_log"]
    assert any("Forecasted demand" in step for step in log)

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import pytest
from unittest.mock import patch
import multi_agent_supply_chain

def test_full_path_high_cost(monkeypatch):
    # Patch agent_ingestion to inject a high cost
    def fake_ingestion(state, **kwargs):
        state["disruption"] = {"type": "supplier_delay", "cost": 60001}
        state.setdefault("decision_log", []).append("Ingestion: Parsed ERP alert.")
        return state
    monkeypatch.setattr(multi_agent_supply_chain, "agent_ingestion", fake_ingestion)
    agent = multi_agent_supply_chain.MultiAgentSupplyChain()
    agent.graph = multi_agent_supply_chain.build_multi_agent_graph()  # Rebuild with patch
    agent.run()
    # Should go through communicator
    log = agent.state["decision_log"]
    assert any("Communicator" in step for step in log)
    assert any("Executor" in step for step in log)
    assert agent.state["approval_required"] is True
    assert agent.state["disruption_cost"] > 50000

def test_full_path_low_cost(monkeypatch):
    # Patch agent_ingestion to inject a low cost
    def fake_ingestion(state, **kwargs):
        state["disruption"] = {"type": "supplier_delay", "cost": 100}
        state.setdefault("decision_log", []).append("Ingestion: Parsed ERP alert.")
        return state
    monkeypatch.setattr(multi_agent_supply_chain, "agent_ingestion", fake_ingestion)
    agent = multi_agent_supply_chain.MultiAgentSupplyChain()
    agent.graph = multi_agent_supply_chain.build_multi_agent_graph()  # Rebuild with patch
    agent.run()
    # Should skip communicator
    log = agent.state["decision_log"]
    assert not any("Communicator" in step for step in log)
    assert any("Executor" in step for step in log)
    assert agent.state["disruption_cost"] <= 50000

def test_simulation_and_planner_called(monkeypatch):
    called = {"simulation": False, "planner": False}
    orig_simulation = multi_agent_supply_chain.agent_simulation
    orig_planner = multi_agent_supply_chain.agent_planner
    def fake_simulation(state, **kwargs):
        called["simulation"] = True
        return orig_simulation(state, **kwargs)
    def fake_planner(state, **kwargs):
        called["planner"] = True
        return orig_planner(state, **kwargs)
    monkeypatch.setattr(multi_agent_supply_chain, "agent_simulation", fake_simulation)
    monkeypatch.setattr(multi_agent_supply_chain, "agent_planner", fake_planner)
    agent = multi_agent_supply_chain.MultiAgentSupplyChain()
    agent.graph = multi_agent_supply_chain.build_multi_agent_graph()  # Rebuild with patch
    agent.run()
    assert called["simulation"]
    assert called["planner"]

def test_executor_always_runs():
    agent = multi_agent_supply_chain.MultiAgentSupplyChain()
    agent.run()
    log = agent.state["decision_log"]
    assert any("Executor" in step for step in log)
