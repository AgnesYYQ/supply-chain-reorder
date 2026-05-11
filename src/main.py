import os
from dotenv import load_dotenv
from src.agent_langgraph import LangGraphSupplyChainAgent

if __name__ == "__main__":
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../config/settings.env'))
    agent = LangGraphSupplyChainAgent()
    agent.run()
