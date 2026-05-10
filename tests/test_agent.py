import unittest
from src.agent import SupplyChainReorderAgent
from src.state import AgentState

class TestSupplyChainReorderAgent(unittest.TestCase):
    def test_agent_flow(self):
        agent = SupplyChainReorderAgent()
        agent.run()
        state = agent.state
        self.assertIn("recommendation", state.data)
        self.assertIsInstance(state.data["recommendation"], int)
        self.assertGreaterEqual(state.data["recommendation"], 0)
        self.assertTrue(len(state.decision_log) > 0)

if __name__ == "__main__":
    unittest.main()
