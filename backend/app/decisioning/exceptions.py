"""
Decisioning Module Exceptions.
"""

class DecisionNotFoundException(Exception):
    def __init__(self, decision_id: str):
        super().__init__(f"Decision not found: {decision_id}")
        self.decision_id = decision_id


class UnauthorizedOverrideException(Exception):
    def __init__(self, actor: str):
        super().__init__(f"Actor '{actor}' is not authorized to override decisions.")
        self.actor = actor


class SimulationProductionMutationException(Exception):
    def __init__(self):
        super().__init__("Simulation cannot mutate production data.")
