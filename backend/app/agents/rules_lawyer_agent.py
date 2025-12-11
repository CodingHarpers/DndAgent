from app.models.schemas import RuleAdjudicationResult, RuleAdjudicationRequest
from typing import Dict, Any
from app.rules.lawyer import RulesLawyer
import json

class RulesLawyerAgent:
    def __init__(self):
        self.lawyer = RulesLawyer()

    def adjudicate(self, player_input: str, context: Dict) -> RuleAdjudicationResult:
        """
        Adjudicates the player's input based on the provided context (game state).
        """
        # Convert context dictionary to a string representation for the lawyer
        # Ensure 'rpg_state' and other keys are included clearly
        context_str = json.dumps(context, indent=2)
        print(f"context_str: {context_str}")
        req = RuleAdjudicationRequest(query=player_input, context=context_str)
        result_text = self.lawyer.check_rule(req)
        print(f"result_text: {result_text}")
        return RuleAdjudicationResult(
            explanation=result_text
        )
