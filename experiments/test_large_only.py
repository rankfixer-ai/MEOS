import sys, os, time
sys.path.insert(0, ".")

from src.core.meos_v0_3_core import BenchmarkRunner, FitnessFunction

original_run = BenchmarkRunner.run_multi_env_benchmark

def large_only_benchmark(self, allele_id, genome, generation=0):
    result = original_run(self, allele_id, genome, generation)
    result["fitness"] = result["env_scores"]["large"]["fitness"]
    return result

BenchmarkRunner.run_multi_env_benchmark = large_only_benchmark

from src.core.meos_v0_3_core import run_evolutionary_loop
from src.selection.selection_engine import SelectionEngine

for f in ["data/meos_v0.3.db", "data/meos_v0.3.db-wal", "data/meos_v0.3.db-shm"]:
    try:
        if os.path.exists(f):
            os.remove(f)
    except:
        pass
time.sleep(0.5)

print("=== EVOLVING FOR LARGE ENVIRONMENT ONLY ===")
r = run_evolutionary_loop(43, 50, SelectionEngine(0.89))
if r:
    print(f"\nLarge-only champion: {r['best_fitness']:.4f}")
else:
    print("\nLarge run failed")

print("\n=== PARETO TEST RESULTS ===")
print("Small-only:  0.9779")
print("Medium-only: 0.9788")
