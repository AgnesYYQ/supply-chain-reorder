import unittest
from unittest.mock import patch, MagicMock
from src.agent_langgraph import LangGraphSupplyChainAgent

class DummyPoint:
    def __init__(self, id, sales):
        self.id = id
        self.payload = {"sales": sales}

class TestLangGraphSupplyChainAgent(unittest.TestCase):
    @patch("qdrant_client.QdrantClient.scroll")
    def test_agent_flow_with_mocked_qdrant(self, mock_scroll):
        # Mock 70 days of sales, ascending id
        points = [DummyPoint(i, 20 + (i % 7)) for i in range(1, 71)]
        mock_scroll.return_value = (points, None)
        agent = LangGraphSupplyChainAgent()
        agent.run()
        state = agent.state
        # Check that the workflow completed and produced a recommendation
        self.assertIn("recommendation", state)
        self.assertIsInstance(state["recommendation"], int)
        self.assertGreaterEqual(state["recommendation"], 0)
        self.assertTrue(len(state["decision_log"]) > 0)
        # Check that the forecast and review steps ran
        self.assertIn("ML forecast for next", " ".join(state["decision_log"]))
        self.assertIn("Review status", " ".join(state["decision_log"]))


