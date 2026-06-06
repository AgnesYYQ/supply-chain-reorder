
from langgraph.graph import StateGraph
# --- Vector DB & Embedding Setup ---
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

# Initialize Chroma client and collection
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection("supply_chain_docs")

# Use a local sentence-transformers model for embedding
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_text(text, chunk_size=50, overlap=10):
    """Chunk text into word-based chunks with overlap."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i+chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

# --- Agent A: Ingestion ---

def agent_ingestion(state: dict, **kwargs):
    # Simulate parsing ERP alert and extracting disruption info
    alert_text = state.get("erp_alert", "Supplier X delayed shipment due to weather. Impact: $60,000.")
    state["disruption"] = {"type": "supplier_delay", "cost": 60000}
    # Chunk and embed alert text, store in Chroma
    chunks = chunk_text(alert_text)
    embeddings = embedder.encode(chunks).tolist()
    ids = [f"alert_{i}" for i in range(len(chunks))]
    # Store in Chroma (idempotent for demo)
    collection.upsert(documents=chunks, embeddings=embeddings, ids=ids)
    state["vector_ids"] = ids
    state.setdefault("decision_log", []).append(f"Ingestion: Parsed ERP alert, chunked and stored {len(chunks)} chunks in vector DB.")
    return state

# --- Agent B: ML Forecast ---

def ml_forecast_agent(state: dict, **kwargs):
    # Retrieve relevant context from vector DB for this disruption
    disruption = state.get("disruption", {})
    query = disruption.get("type", "supplier_delay")
    # Embed query and search Chroma
    query_emb = embedder.encode([query])[0].tolist()
    results = collection.query(query_embeddings=[query_emb], n_results=2)
    retrieved_chunks = results.get("documents", [[]])[0]
    state["retrieved_context"] = retrieved_chunks
    state.setdefault("decision_log", []).append(f"ML Agent: Retrieved {len(retrieved_chunks)} relevant chunks from vector DB.")

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
        f"Planner: Evaluated options, recommended 'reroute_logistics', cost={state['disruption_cost']}"
    )
    return state

# --- Agent D: Second Opinion (independent analysis) ---
def agent_second_opinion(state: dict, **kwargs):
    """
    Independent agent that scores each mitigation option across multiple
    dimensions to produce a genuinely independent recommendation.

    Scoring factors (each 0-10):
      - cost_effectiveness: Minimises financial impact
      - speed: How fast the option restores operations
      - long_term_viability: Whether it prevents repeat disruptions
      - risk: Low risk of negative side effects (inverted — higher = safer)

    The Second Opinion uses deliberately different weighting than the Planner
    so it can disagree intelligently rather than just at a threshold boundary.
    """
    disruption = state.get("disruption", {})
    cost = disruption.get("cost", 0)
    disruption_type = disruption.get("type", "supplier_delay")

    # --- Score each candidate option independently ---
    options = {
        "reroute_logistics": {
            "cost_effectiveness": 8 if cost < 30000 else 4,
            "speed": 9,
            "long_term_viability": 3,
            "risk": 8,
        },
        "change_supplier": {
            "cost_effectiveness": 3 if cost < 20000 else 7,
            "speed": 2,
            "long_term_viability": 9,
            "risk": 5,
        },
    }

    # Dynamically add options based on disruption context
    if disruption_type == "supplier_delay":
        options["expedite_shipping"] = {
            "cost_effectiveness": 5,
            "speed": 7,
            "long_term_viability": 2,
            "risk": 7,
        }

    if cost > 50000:
        options["split_order"] = {
            "cost_effectiveness": 6,
            "speed": 4,
            "long_term_viability": 6,
            "risk": 6,
        }

    # Weights — deliberately different from what a Planner might use.
    # Second Opinion favours long-term health over short-term speed.
    weights = {
        "cost_effectiveness": 0.25,
        "speed": 0.15,
        "long_term_viability": 0.40,
        "risk": 0.20,
    }

    scored = {}
    for name, dims in options.items():
        score = sum(dims[d] * weights[d] for d in dims)
        scored[name] = round(score, 2)

    best = max(scored, key=scored.get)
    sorted_options = sorted(scored.items(), key=lambda x: -x[1])

    # Build an explainable trace
    detail_lines = []
    for name, s in sorted_options:
        dims = options[name]
        parts = " | ".join(f"{k}={dims[k]}" for k in dims)
        detail_lines.append(f"  {name}: {s}  ({parts})")
    detail = "\n".join(detail_lines)

    reasoning = (
        f"Scored {len(scored)} options with weights "
        f"cost={weights['cost_effectiveness']}, speed={weights['speed']}, "
        f"long_term={weights['long_term_viability']}, risk={weights['risk']}.\n"
        f"{detail}\n"
        f"→ Selected '{best}' (score={scored[best]})"
    )

    state["second_opinion"] = best
    state["second_opinion_scores"] = scored
    state["second_opinion_reasoning"] = reasoning
    state.setdefault("decision_log", []).append(
        f"Second Opinion: Recommended '{best}' (score={scored[best]}). "
        f"Runner-up: {sorted_options[1][0]} ({sorted_options[1][1]})."
    )
    return state

# --- Agent E: Reviewer (4-Eyes Principle) ---
def agent_reviewer(state: dict, **kwargs):
    """
    Four-eyes check: compares Planner recommendation vs. Second Opinion.

    Now considers the **score gap** from the Second Opinion's analysis:
      - If scores are near-tied (gap < 0.5), disagreement is weak → may still
        auto-approve for low-cost items.
      - If scores decisively favour a different option (gap >= 1.0), the
        disagreement is strong and always escalates.
    """
    planner_option = state.get("best_option", "unknown")
    second_option = state.get("second_opinion", "unknown")
    scores = state.get("second_opinion_scores", {})
    cost = state.get("disruption_cost", 0)

    consensus = planner_option == second_option
    high_cost = cost > 50000

    # How decisively does the Second Opinion disagree?
    if planner_option in scores and second_option in scores and not consensus:
        score_gap = abs(scores[planner_option] - scores[second_option])
    else:
        score_gap = 0.0

    if consensus and not high_cost:
        state["review_verdict"] = "approved"
        state["review_notes"] = (
            f"4-Eyes OK: Both recommend '{planner_option}', "
            f"cost=${cost} within threshold."
        )
        state["approval_required"] = False

    elif consensus and high_cost:
        state["review_verdict"] = "escalated_high_cost"
        state["review_notes"] = (
            f"4-Eyes: Both agree on '{planner_option}' but cost=${cost} exceeds "
            f"$50k threshold — escalating for human approval."
        )
        state["approval_required"] = True

    elif not consensus and score_gap < 0.5 and not high_cost:
        # Weak disagreement on low-cost item — still safe to auto-approve
        state["review_verdict"] = "approved"
        state["review_notes"] = (
            f"4-Eyes: Planner chose '{planner_option}', Second Opinion chose "
            f"'{second_option}' (gap={score_gap:.2f}) but cost=${cost} is low — "
            f"near-tie, auto-approved."
        )
        state["approval_required"] = False

    else:
        # Strong disagreement OR high cost — escalate
        severity = "strong" if score_gap >= 1.0 else "moderate"
        state["review_verdict"] = "escalated_conflict"
        state["review_notes"] = (
            f"4-Eyes {severity.upper()} CONFLICT: Planner recommends "
            f"'{planner_option}' but Second Opinion recommends "
            f"'{second_option}' (score gap={score_gap:.2f}, cost=${cost}). "
            f"Escalating for human review."
        )
        state["approval_required"] = True

    state.setdefault("decision_log", []).append(
        f"Reviewer (4-Eyes): {state['review_notes']}"
    )
    return state

# --- Agent F: Communicator ---
def agent_communicator(state: dict, **kwargs):
    # Draft human-in-the-loop approval
    state.setdefault("decision_log", []).append(
        f"Communicator: Human approval requested. Verdict={state.get('review_verdict')}. "
        f"Notes={state.get('review_notes')}"
    )
    return state

# --- Agent G: Executor ---
def agent_executor(state: dict, **kwargs):
    best_option = state.get("best_option", "unknown")
    state.setdefault("decision_log", []).append(
        f"Executor: Executed mitigation '{best_option}'. "
        f"Review verdict: {state.get('review_verdict', 'N/A')}."
    )
    return state

def build_multi_agent_graph():
    graph = StateGraph(dict)
    graph.add_node("ingestion", agent_ingestion)
    graph.add_node("ml_forecast", ml_forecast_agent)
    graph.add_node("planner", agent_planner)
    graph.add_node("second_opinion", agent_second_opinion)
    graph.add_node("reviewer", agent_reviewer)
    graph.add_node("communicator", agent_communicator)
    graph.add_node("executor", agent_executor)

    # Linear flow: Ingestion -> ML Forecast -> Planner
    graph.add_edge("ingestion", "ml_forecast")
    graph.add_edge("ml_forecast", "planner")

    # Planner -> Second Opinion (independent parallel analysis)
    graph.add_edge("planner", "second_opinion")

    # Second Opinion -> Reviewer (4-Eyes)
    graph.add_edge("second_opinion", "reviewer")

    # Reviewer conditional: if 4-eyes approved, go directly to Executor.
    # Otherwise (conflict or high-cost) escalate to Communicator.
    def reviewer_router(state: dict, **kwargs):
        verdict = state.get("review_verdict", "escalated_conflict")
        if verdict == "approved":
            return "executor"
        else:
            return "communicator"

    graph.add_conditional_edges("reviewer", reviewer_router, {
        "executor": "executor",
        "communicator": "communicator",
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
