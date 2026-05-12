from langgraph.graph import StateGraph

# --- Agent A: Ingestion ---
def agent_ingestion(state: dict, **kwargs):
    # Parse ERP disruption alert, extract disruption info
    state["disruption"] = {"type": "supplier_delay", "cost": 60000}
    state.setdefault("decision_log", []).append("Ingestion: Parsed ERP alert.")
    return state

# --- Agent B: ML Forecast ---
def ml_forecast_agent(state: dict, **kwargs):
    # If sales_history and lead_time are present, try a neural network forecast (LSTM)
    sales = state.get("sales_history")
    lead_time = state.get("lead_time", 2)
    if sales and isinstance(sales, list) and len(sales) > lead_time:
        try:
            import numpy as np
            from tensorflow import keras
            from tensorflow.keras import layers
            # Prepare data: use last N-1 as input, last as target
            X = np.array(sales[:-1]).reshape(-1, 1, 1)
            y = np.array(sales[1:]).reshape(-1, 1)
            # Build simple LSTM model
            model = keras.Sequential([
                layers.LSTM(8, input_shape=(1, 1)),
                layers.Dense(1)
            ])
            model.compile(optimizer='adam', loss='mse')
            model.fit(X, y, epochs=20, verbose=0)
            # Forecast next value using last value as input
            last_val = np.array(sales[-1]).reshape(1, 1, 1)
            forecast = float(model.predict(last_val, verbose=0)[0][0])
            state["forecast"] = forecast
            state.setdefault("decision_log", []).append(f"Simulation: LSTM forecasted demand = {forecast:.2f}")
        except ImportError:
            # Fallback: mean of last 'lead_time' sales
            forecast = sum(sales[-lead_time:]) / lead_time
            state["forecast"] = forecast
            state.setdefault("decision_log", []).append(f"Simulation: Fallback mean forecast = {forecast}")
    else:
        state.setdefault("decision_log", []).append("Simulation: No sales data, skipped forecast.")
    state["mitigation_options"] = ["reroute_logistics", "change_supplier"]
    state.setdefault("decision_log", []).append("Simulation: Ran what-if scenarios.")
    return state

# --- Agent C: Planner ---
def agent_planner(state: dict, **kwargs):
    # Evaluate cost/benefit of options
    state["best_option"] = "reroute_logistics"
    state["disruption_cost"] = state["disruption"]["cost"]
    state.setdefault("decision_log", []).append(
        f"Planner: Evaluated options, cost={state['disruption_cost']}"
    )
    return state

# --- Agent D: Communicator ---
def agent_communicator(state: dict, **kwargs):
    # Draft human-in-the-loop approval
    state["approval_required"] = True
    state.setdefault("decision_log", []).append("Communicator: Drafted approval request.")
    return state

# --- Agent E: Executor ---
def agent_executor(state: dict, **kwargs):
    # Auto-execute or finalize
    state.setdefault("decision_log", []).append("Executor: Auto-executed mitigation.")
    return state

def build_multi_agent_graph():
    graph = StateGraph(dict)
    graph.add_node("ingestion", agent_ingestion)
    graph.add_node("ml_forecast", ml_forecast_agent)
    graph.add_node("planner", agent_planner)
    graph.add_node("communicator", agent_communicator)
    graph.add_node("executor", agent_executor)

    # Linear flow: Ingestion -> Simulation -> Planner
    graph.add_edge("ingestion", "ml_forecast")
    graph.add_edge("ml_forecast", "planner")

    # Conditional: If cost > 50k, go to Communicator, else Executor
    def planner_router(state: dict, **kwargs):
        if state.get("disruption_cost", 0) > 50000:
            return "communicator"
        else:
            return "executor"
    graph.add_conditional_edges("planner", planner_router, {
        "communicator": "communicator",
        "executor": "executor"
    })

    # After Communicator, always go to Executor
    graph.add_edge("communicator", "executor")

    graph.set_entry_point("ingestion")
    return graph

class MultiAgentSupplyChain:
    def __init__(self):
        self.state = {"decision_log": []}
        self.graph = build_multi_agent_graph()

    def run(self):
        compiled = self.graph.compile()
        self.state = compiled.invoke(self.state)
        self.explain()

    def explain(self):
        print("\n--- Decision Trace ---")
        for step in self.state.get("decision_log", []):
            print(step)
        print("\nFinal Decision State:")
        print(self.state)

if __name__ == "__main__":
    agent = MultiAgentSupplyChain()
    agent.run()
