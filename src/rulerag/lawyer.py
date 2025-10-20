class RulesLawyer:
    def adjudicate(self, action_intent, rule_json, die_roll):
        """
        Applies strict logic to determine the outcome.
        Does NOT generate flavor text.
        """
        # Placeholder implementation
        if die_roll >= rule_json.get('difficulty_class', 10):
            return {"outcome": "success", "effect": rule_json.get('success_outcome')}
        return {"outcome": "failure"}
