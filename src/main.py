from src.agent import SupplyChainReorderAgent
from dotenv import load_dotenv
import os

if __name__ == "__main__":
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../config/settings.env'))
    agent = SupplyChainReorderAgent()
    agent.run()
