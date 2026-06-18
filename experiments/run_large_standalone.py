import sys, os
sys.path.insert(0, ".")
from src.core.meos_v0_3_core import BenchmarkRunner, FitnessFunction

_original = BenchmarkRunner.run_multi_env_benchmark
def _large_only(self, allele_id, genome, generation=0):
    r = _original(self, allele_id, genome, generation)
    r["fitness"] = r["env_scores"]["large"]["fitness"]
    return r
BenchmarkRunner.run_multi_env_benchmark = _large_only

from src.core.meos_v0_3_core import run_evolutionary_loop
from src.selection.selection_engine import SelectionEngine

print("=== LARGE ENVIRONMENT ONLY ===")
r = run_evolutionary_loop(43, 50, SelectionEngine(0.89))
if r:
    lf = r["best_fitness"]
    print(f"\nLarge-only champion: {lf:.4f}")
    print(f"\n=== PARETO RESULTS ===")
    print(f"Small-only:  0.9779")
    print(f"Medium-only: 0.9788")
    print(f"Large-only:  {lf:.4f}")
    if lf > 0.985:
        print("\nVERDICT: Pareto tradeoff - each env can exceed combined ceiling")
    else:
        print("\nVERDICT: Intrinsic ceiling ~0.978 per environment")
