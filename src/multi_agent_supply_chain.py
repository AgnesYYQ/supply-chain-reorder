from langgraph.graph import StateGraph

# --- Agent A: Ingestion ---
def agent_ingestion(state: dict, **kwargs):
    # Parse ERP disruption alert, extract disruption info
    state["disruption"] = {"type": "supplier_delay", "cost": 60000}
    state.setdefault("decision_log", []).append("Ingestion: Parsed ERP alert.")
    return state

# --- Agent B: Simulation ---
def agent_simulation(state: dict, **kwargs):
    # Look up mitigation strategies, run what-if scenarios
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
    graph.add_node("simulation", agent_simulation)
    graph.add_node("planner", agent_planner)
    graph.add_node("communicator", agent_communicator)
    graph.add_node("executor", agent_executor)

    # Linear flow: Ingestion -> Simulation -> Planner
    graph.add_edge("ingestion", "simulation")
    graph.add_edge("simulation", "planner")

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
