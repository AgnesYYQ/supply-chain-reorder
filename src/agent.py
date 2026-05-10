from src.nodes import (
    gather_data_node,
    forecast_node,
    optimize_node,
    review_node,
    execute_node
)
from src.state import AgentState

class SupplyChainReorderAgent:
    def __init__(self):
        self.state = AgentState()
        self.nodes = [
            gather_data_node,
            forecast_node,
            optimize_node,
            review_node,
            execute_node
        ]

    def run(self):
        for node in self.nodes:
            node(self.state)
        self.state.explain()
