# Supply Chain Reorder Agent

An agentic AI system to help supply chain planners decide how much inventory to reorder. Built with LangGraph for workflow orchestration, modular nodes, and explainable state management.

## Features
- LangGraph workflow for modular, extensible agent logic
- Nodes for data ingestion (API/vector DB), ML forecasting (API), optimization, human review, and execution
- State management for explainability and traceability
- Ready for integration with ERP APIs, ML models, and data sources
- Configurable business rules
- Unit tests and production-ready structure

## Workflow Overview

The agent is orchestrated by LangGraph. The logical flow is:

1. **Data Ingestion**: Parses disruption input and stores embedded chunks in Chroma
2. **ML Forecasting**: Retrieves vector context and optionally forecasts demand from `sales_history`
3. **Planner**: Chooses a mitigation path and records disruption cost
4. **Review**: Flags expensive disruptions for human approval
5. **Execution**: Finalizes mitigation execution and logs the outcome

All calculations and decisions are logged for explainability. You can extend any node to connect to real APIs, databases, or ML endpoints as needed.

## Setup
1. Clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Configure settings in `config/`
4. Run the agent: `python src/main.py`

## Project Structure
- `src/` – Agent logic, LangGraph workflow, state management
- `tests/` – Unit tests
- `config/` – Configuration files
- `.github/` – Copilot instructions

## Infrastructure Diagram

This diagram shows the runtime components: the input, embedding layer, vector store, graph execution, and final decision log.

```mermaid
flowchart LR
	ERP["ERP Alert / Sales Input"] --> ING["Ingestion Node"]
	ING --> EMB["SentenceTransformer Embeddings"]
	EMB --> CHR["Chroma Vector DB"]
	ING --> FLOW["LangGraph StateGraph"]
	CHR --> ML["ML Forecast Node"]
	FLOW --> ML
	ML --> PLN["Planner Node"]
	PLN -->|cost > 50k| COM["Communicator Node"]
	PLN -->|cost <= 50k| EXE["Executor Node"]
	COM --> EXE
	EXE --> LOG["Decision Log / Final State"]
	LOG -.->|Explainability| FLOW
	style ERP fill:#d9edf7,stroke:#1b4d72,stroke-width:1.5px,color:#111
	style CHR fill:#e8f5e9,stroke:#2e7d32,stroke-width:1.5px,color:#111
	style FLOW fill:#fff3cd,stroke:#8a6d3b,stroke-width:1.5px,color:#111
	style LOG fill:#fce4ec,stroke:#ad1457,stroke-width:1.5px,color:#111
```

## State Diagram

This diagram shows the logical decision path inside the LangGraph workflow.

```mermaid
flowchart TD
	A["Data Ingestion (API/Vector DB)"] --> B["ML Forecast (API)"]
	B --> C["Planner"]
	C -->|cost > 50k| D["Review (Human Approval)"]
	C -->|cost <= 50k| E["Execute (ERP API)"]
	D --> E
	E --> F["State/Decision Log"]
	F -.->|Explainability| A
	style F fill:#f9f,stroke:#222,stroke-width:2px,color:#111
	style D fill:#ff9,stroke:#222,stroke-width:2px,color:#111
	style A fill:#bbf,stroke:#222,stroke-width:2px,color:#111
	style B fill:#bbf,stroke:#222,stroke-width:2px,color:#111
	style C fill:#bbf,stroke:#222,stroke-width:2px,color:#111
	style E fill:#bbf,stroke:#222,stroke-width:2px,color:#111
```

## Extending the Multi-Agent Workflow

The code in `src/multi_agent_supply_chain.py` is organized around these nodes:

- `agent_ingestion`: parses disruption input and stores embedded chunks in Chroma
- `ml_forecast_agent`: retrieves vector context and produces a forecast when sales history is available
- `agent_planner`: chooses the mitigation path and computes disruption cost
- `agent_communicator`: flags approvals for human review when the disruption is expensive
- `agent_executor`: finalizes mitigation execution

## Example Forecast Path

If you want to exercise the forecast branch, seed the agent with `sales_history` and `lead_time` before calling `run()`:

```python
from src.multi_agent_supply_chain import MultiAgentSupplyChain

agent = MultiAgentSupplyChain()
agent.state = {
	"sales_history": [120, 132, 128, 140, 138],
	"lead_time": 2,
	"decision_log": []
}
agent.run()

print(agent.state.get("forecast"))
print(agent.state.get("decision_log"))
```

If TensorFlow is installed, the forecast node will try an LSTM-based prediction. Otherwise, it falls back to the mean of the most recent `lead_time` sales values.

## Usage
Edit `config/` for your environment and run the agent. See `src/main.py` for the entry point and flow.

## License
MIT
