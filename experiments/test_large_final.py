import sys, os
sys.path.insert(0, ".")

for f in ["data/meos_v0.3.db", "data/meos_v0.3.db-wal", "data/meos_v0.3.db-shm"]:
    try: os.remove(f)
    except: pass

from src.core.meos_v0_3_core import BenchmarkRunner, FitnessFunction
original = BenchmarkRunner.run_multi_env_benchmark
def large_only(self, allele_id, genome, generation=0):
    r = original(self, allele_id, genome, generation)
    r["fitness"] = r["env_scores"]["large"]["fitness"]
    return r
BenchmarkRunner.run_multi_env_benchmark = large_only

from src.core.meos_v0_3_core import run_evolutionary_loop
from src.selection.selection_engine import SelectionEngine

print("=== EVOLVING FOR LARGE ENVIRONMENT ONLY ===")
r = run_evolutionary_loop(43, 50, SelectionEngine(0.89))
if r:
    lf = r["best_fitness"]
    print(f"Large-only champion: {lf:.4f}")
    print()
    print("=== FINAL PARETO RESULTS ===")
    print(f"Small-only:  0.9779")
    print(f"Medium-only: 0.9788")
    print(f"Large-only:  {lf:.4f}")
    print()
    if lf > 0.985:
        print("VERDICT: Combined ceiling is a PARETO TRADEOFF")
    else:
        print("VERDICT: Each environment has its own INTRINSIC CEILING ~0.978")
