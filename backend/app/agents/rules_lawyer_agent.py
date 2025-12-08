from app.models.schemas import RuleAdjudicationResult
from typing import Dict, Any

class RulesLawyerAgent:
    def adjudicate(self, player_input: str, context: Dict) -> RuleAdjudicationResult:
        # Simplistic keyword check for demo
        decision = "ALLOWED"
        explanation = "Action proceeds normally."
        
        if "attack" in player_input.lower():
            decision = "ROLL_CHECK"
            explanation = "You need to roll for attack."
            
        return RuleAdjudicationResult(
            decision=decision,
            explanation=explanation,
            required_rolls=["d20"] if decision == "ROLL_CHECK" else []
        )
