import os
import sys
from dotenv import load_dotenv

# Ensure the project root is on the path so 'python src/main.py' works
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.multi_agent_supply_chain import MultiAgentSupplyChain

if __name__ == "__main__":
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../config/settings.env'))
    agent = MultiAgentSupplyChain()
    agent.run()
