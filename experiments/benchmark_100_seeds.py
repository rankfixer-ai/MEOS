import sys, os, time
sys.path.insert(0, ".")
from src.core.meos_v0_3_core import run_evolutionary_loop
from src.selection.selection_engine import SelectionEngine
import statistics

results = []
for seed in range(100):
    db_path = "data/meos_v0.3.db"
    for attempt in range(5):
        try:
            for f in [db_path, db_path + "-wal", db_path + "-shm"]:
                if os.path.exists(f):
                    os.remove(f)
            break
        except PermissionError:
            time.sleep(0.5)
    r = run_evolutionary_loop(seed, 100, SelectionEngine(0.89))
    results.append(r["best_fitness"])
    if (seed + 1) % 10 == 0:
        print(f"  {seed+1}/100 complete...")

fitnesses = sorted(results)
print("\n=== 100-SEED BENCHMARK ===")
print(f"Seeds:    100")
print(f"Mean:     {statistics.mean(fitnesses):.4f}")
print(f"Median:   {statistics.median(fitnesses):.4f}")
print(f"StdDev:   {statistics.stdev(fitnesses):.4f}")
print(f"Min:      {min(fitnesses):.4f}")
print(f"Max:      {max(fitnesses):.4f}")
print(f"P90:      {fitnesses[89]:.4f}")
print(f"P95:      {fitnesses[94]:.4f}")
print(f">0.97:    {sum(1 for f in fitnesses if f > 0.97)}/100")
print(f">0.975:   {sum(1 for f in fitnesses if f > 0.975)}/100")
print(f">0.95:    {sum(1 for f in fitnesses if f > 0.95)}/100")
