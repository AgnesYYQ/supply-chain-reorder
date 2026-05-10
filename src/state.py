from typing import Any, Dict, List

class AgentState:
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.decision_log: List[str] = []

    def log(self, message: str):
        self.decision_log.append(message)

    def explain(self):
        print("\n--- Decision Trace ---")
        for step in self.decision_log:
            print(step)
        print("\nFinal Recommendation:")
        print(self.data.get("recommendation", "No recommendation computed."))
