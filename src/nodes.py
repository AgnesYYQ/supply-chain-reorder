import os
import requests
from typing import Any
from src.state import AgentState

# --- Node 1: Gather Data ---
def gather_data_node(state: AgentState):
    # Placeholder: Replace with real data fetching logic
    state.data["inventory"] = 100
    state.data["sales_velocity"] = 20
    state.data["lead_time"] = 7
    state.log(f"Gathered data: inventory={state.data['inventory']}, sales_velocity={state.data['sales_velocity']}, lead_time={state.data['lead_time']}")

# --- Node 2: Forecast ---
def forecast_node(state: AgentState):
    # Placeholder: Replace with real ML/LLM call
    # Example: requests.post(os.getenv('ML_MODEL_ENDPOINT'), json=state.data)
    forecast = state.data["sales_velocity"] * state.data["lead_time"]
    state.data["forecast"] = forecast
    state.log(f"Forecasted demand for next period: {forecast}")

# --- Node 3: Optimize ---
def optimize_node(state: AgentState):
    # Placeholder: Replace with real business rules
    min_stock = 50
    max_stock = 200
    recommended = max(min_stock, min(state.data["forecast"], max_stock))
    state.data["recommendation"] = recommended
    state.log(f"Optimized reorder amount: {recommended}")

# --- Node 4: Review (Human-in-the-loop) ---
def review_node(state: AgentState):
    # Placeholder: In production, trigger human review for risky/large orders
    if state.data["recommendation"] > 150:
        state.log("Human review required: large order.")
        # Simulate approval
        state.data["reviewed"] = True
    else:
        state.data["reviewed"] = False
    state.log(f"Review status: {state.data['reviewed']}")

# --- Node 5: Execute ---
def execute_node(state: AgentState):
    # Placeholder: Replace with real ERP API call
    if state.data.get("reviewed", False):
        # Simulate ERP call
        # requests.post(os.getenv('ERP_API_URL'), headers={"Authorization": os.getenv('ERP_API_KEY')}, json={...})
        state.log(f"Executed purchase order for {state.data['recommendation']} units (ERP API call simulated).")
    else:
        state.log("No execution needed or not approved.")
