class SelectionEngine:
    def __init__(self, target_threshold: float = 0.89, stability_weight: float = 0.3):
        self.target_threshold = target_threshold
        self.w_stability = stability_weight
        self.w_fitness = 1.0 - stability_weight

    def evaluate_candidate(self, p_fit: float, p_stab: float, c_fit: float, c_stab: float) -> tuple:
        fit_delta  = c_fit - p_fit
        stab_delta = c_stab - p_stab

        # Both improved or held
        if fit_delta >= 0 and stab_delta >= 0:
            return True, "PROMOTED"

        # Fitness improved meaningfully, stability drop is minor
        if fit_delta > 0.005 and stab_delta > -0.02:
            return True, "PROMOTED"

        # Compensatory: tiny fitness drop offset by large stability gain
        if fit_delta > -0.02 and stab_delta > abs(fit_delta) * 2.0:
            return True, "PROMOTED"

        if c_fit < p_fit:
            return False, "REJECTED_FITNESS"

        return False, "REJECTED_THRESHOLD"

    def calculate_combined_score(self, fitness: float, stability: float) -> float:
        return self.w_fitness * fitness + self.w_stability * stability

    def calculate_novelty(self, candidate_genome, archive):
        # Placeholder for V0.4 logic
        return 0.0
