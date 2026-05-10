# Supply Chain Reorder Agent

A production-grade, agentic AI system to help supply chain planners decide how much inventory to reorder. Built with LangGraph, modular nodes, and explainable state management.

## Features
- Modular agent with nodes for data gathering, forecasting, optimization, human review, and execution
- State management for explainability and traceability
- Stubs for integration with ERP APIs, ML models, and data sources
- Configurable business rules
- Unit tests and production-ready structure

## Setup
1. Clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Configure settings in `config/`
4. Run the agent: `python src/main.py`

## Project Structure
- `src/` – Agent logic, nodes, state management
- `tests/` – Unit tests
- `config/` – Configuration files
- `.github/` – Copilot instructions


## Architecture Diagrams

### Agentic Flow

```mermaid
flowchart TD
	A["Gather Data"] --> B["Forecast Demand"]
	B --> C["Optimize Order Quantity"]
	C --> D["Review (Human Approval)"]
	D --> E["Execute (ERP API)"]
	E --> F["State/Decision Log"]
	F -.->|Explainability| A
	style F fill:#f9f,stroke:#222,stroke-width:2px,color:#111
	style D fill:#ff9,stroke:#222,stroke-width:2px,color:#111
	style A fill:#bbf,stroke:#222,stroke-width:2px,color:#111
	style B fill:#bbf,stroke:#222,stroke-width:2px,color:#111
	style C fill:#bbf,stroke:#222,stroke-width:2px,color:#111
	style E fill:#bbf,stroke:#222,stroke-width:2px,color:#111
```

### Python Class Architecture

```mermaid
classDiagram
	class SupplyChainReorderAgent {
		-AgentState state
		-list nodes
		+run()
	}
	class AgentState {
		-dict data
		-list decision_log
		+log(message)
		+explain()
	}
	class gather_data_node {
		+__call__(state)
	}
	class forecast_node {
		+__call__(state)
	}
	class optimize_node {
		+__call__(state)
	}
	class review_node {
		+__call__(state)
	}
	class execute_node {
		+__call__(state)
	}
	SupplyChainReorderAgent --> AgentState
	SupplyChainReorderAgent --> gather_data_node
	SupplyChainReorderAgent --> forecast_node
	SupplyChainReorderAgent --> optimize_node
	SupplyChainReorderAgent --> review_node
	SupplyChainReorderAgent --> execute_node
	AgentState <.. gather_data_node : uses
	AgentState <.. forecast_node : uses
	AgentState <.. optimize_node : uses
	AgentState <.. review_node : uses
	AgentState <.. execute_node : uses
```

## Usage
Edit `config/` for your environment and run the agent. See `src/main.py` for the entry point and flow.

## License
MIT
