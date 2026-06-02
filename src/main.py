import os
from dotenv import load_dotenv
from src.multi_agent_supply_chain import MultiAgentSupplyChain

if __name__ == "__main__":
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../config/settings.env'))
    agent = MultiAgentSupplyChain()
    agent.run()
