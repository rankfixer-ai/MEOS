import sys
sys.path.insert(0, ".")
from src.core.meos_v0_3_core import run_evolutionary_loop
from src.selection.selection_engine import SelectionEngine

results = []
for seed in range(40, 50):
    print(f"=== Seed {seed} ===")
    r = run_evolutionary_loop(seed, 100, SelectionEngine(0.89))
    results.append((seed, r["best_fitness"], r["improvement"]))
    print(f"SEED_RESULT: {seed} {r['best_fitness']:.4f} {r['improvement']:.2%}")

print("\n=== SUMMARY ===")
fitnesses = [r[1] for r in results]
print(f"Mean: {sum(fitnesses)/len(fitnesses):.4f}")
print(f"Max:  {max(fitnesses):.4f}")
print(f"Min:  {min(fitnesses):.4f}")
print(f">0.97: {sum(1 for f in fitnesses if f > 0.97)}/10")
print(f">0.95: {sum(1 for f in fitnesses if f > 0.95)}/10")
