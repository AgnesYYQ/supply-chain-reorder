

from langgraph.graph import StateGraph

# --- Node 1: Data Ingestion (Qdrant) ---
def ingest_data(state: dict, **kwargs):
    import qdrant_client
    client = qdrant_client.QdrantClient(url="http://localhost:6333")
    result, _ = client.scroll(collection_name="sales", limit=70, with_payload=True, with_vectors=False, offset=None)
    points = sorted(result, key=lambda p: p.id)
    sales_history = [point.payload["sales"] for point in points]
    state["sales_history"] = sales_history
    state["inventory"] = 100
    state["lead_time"] = 7
    state["service_level"] = 0.98
    state["unit_cost"] = 10
    state["order_cost"] = 50
    state["holding_cost"] = 2
    state.setdefault("decision_log", []).append(
        f"Ingested data: inventory={state['inventory']}, lead_time={state['lead_time']}, sales_history(last 5)={state['sales_history'][-5:]}"
    )
    return state

# --- Node 2: ML Forecasting (stub) ---
def ml_forecast(state: dict, **kwargs):
    sales_history = state["sales_history"]
    lead_time = state["lead_time"]
    forecast = int(sum(sales_history[-lead_time:]) / lead_time)
    state["forecast"] = forecast
    state.setdefault("decision_log", []).append(f"ML forecast for next {lead_time} days: {forecast}")
    return state

# --- Node 3: Optimize ---
def optimize(state: dict, **kwargs):
    demand = sum(state["sales_history"]) / len(state["sales_history"])
    safety_stock = 10  # Fixed for demo
    reorder_qty = max(0, state["forecast"] + safety_stock - state["inventory"])
    state["recommendation"] = reorder_qty
    state.setdefault("decision_log", []).append(f"Dummy EOQ, Safety Stock: {safety_stock}, Recommended reorder: {reorder_qty}")
    return state

# --- Node 4: Review ---
def review(state: dict, **kwargs):
    threshold = 150
    if state["recommendation"] > threshold:
        state.setdefault("decision_log", []).append(f"Human review required: large order ({state['recommendation']}).")
        state["reviewed"] = True
    else:
        state["reviewed"] = False
    state.setdefault("decision_log", []).append(f"Review status: {state['reviewed']}")
    return state

# --- Node 5: Execute ---
def execute(state: dict, **kwargs):
    if state.get("reviewed", False):
        state.setdefault("decision_log", []).append(f"Executed purchase order for {state['recommendation']} units (ERP API call simulated).")
    else:
        state.setdefault("decision_log", []).append("No execution needed or not approved.")
    return state

# Build the LangGraph workflow
def build_supply_chain_graph():
    graph = StateGraph(dict)
    graph.add_node("ingest_data", ingest_data)
    graph.add_node("ml_forecast", ml_forecast)
    graph.add_node("optimize", optimize)
    graph.add_node("review", review)
    graph.add_node("execute", execute)
    graph.add_edge("ingest_data", "ml_forecast")
    graph.add_edge("ml_forecast", "optimize")
    graph.add_edge("optimize", "review")
    graph.add_edge("review", "execute")
    graph.set_entry_point("ingest_data")
    return graph


class LangGraphSupplyChainAgent:
    def __init__(self):
        self.state = {"decision_log": []}
        self.graph = build_supply_chain_graph()

    def run(self):
        compiled = self.graph.compile()
        self.state = compiled.invoke(self.state)
        self.explain()

    def explain(self):
        print("\n--- Decision Trace ---")
        for step in self.state.get("decision_log", []):
            print(step)
        print("\nFinal Recommendation:")
        print(self.state.get("recommendation", "No recommendation computed."))

class LangGraphSupplyChainAgent:
    def __init__(self):
        self.state = {"decision_log": []}
        self.graph = build_supply_chain_graph()

    def run(self):
        compiled = self.graph.compile()
        self.state = compiled.invoke(self.state)
        self.explain()

    def explain(self):
        print("\n--- Decision Trace ---")
        for step in self.state.get("decision_log", []):
            print(step)
        print("\nFinal Recommendation:")
        print(self.state.get("recommendation", "No recommendation computed."))
