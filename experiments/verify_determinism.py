import sys
sys.path.insert(0, ".")
from src.core.meos_v0_3_core import BenchmarkRunner, FitnessFunction

GENOME = {
    "parallelism": 1, "cache_enabled": False, "cache_size": 0,
    "reranking_enabled": False, "batch_size": 10,
    "timeout_seconds": 30, "max_results": 50,
    "scoring_strategy": "cosine", "retrieval_depth": 10,
    "cache_eviction_policy": "lru", "ranking_model_temp": 0.5
}

results = []
for i in range(5):
    runner = BenchmarkRunner(FitnessFunction())
    r = runner.run_multi_env_benchmark("verify", GENOME)
    results.append(r['fitness'])
    print(f"  Run {i+1}: {r['fitness']:.10f}")

if len(set(round(r, 10) for r in results)) == 1:
    print(f"\nPASS: All identical ({results[0]:.10f})")
else:
    print(f"\nFAIL - variance detected: {[round(r,10) for r in results]}")
    print("The _generate_queries leak is still active on this file.")
