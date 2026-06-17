"""
MEOS V0.3 - Champion Replay
Tests the stability of the 0.9600 champion genome.
"""

import sqlite3
import json
import random
import time
import statistics
import hashlib
from typing import Dict, List, Any

# ============================================================
# SEARCH ENGINE
# ============================================================

class SearchEngine:
    def __init__(self, genome: Dict, seed: int = 42):
        self.parallelism = genome.get("parallelism", 1)
        self.cache_enabled = genome.get("cache_enabled", False)
        self.cache_size = genome.get("cache_size", 0)
        self.reranking_enabled = genome.get("reranking_enabled", False)
        self.batch_size = genome.get("batch_size", 10)
        self.timeout = genome.get("timeout_seconds", 30)
        self.max_results = genome.get("max_results", 50)
        self.seed = seed
        self.random = random.Random(seed)
        self.cache = {}

    def search(self, query: str, sources: List[str]) -> List[Dict]:
        if self.cache_enabled and query in self.cache:
            return self.cache[query][:self.max_results]
        latency = 0.05 * max(1, len(sources) / max(1, self.parallelism))
        time.sleep(min(latency, self.timeout))
        results = []
        for i, source in enumerate(sources[:self.batch_size]):
            self.random.seed(hash(query + source + str(i) + str(self.seed)) % 10000)
            results.append({
                "source": source,
                "title": f"{source}: {query[:20]}...",
                "relevance": self.random.uniform(0.3, 0.9)
            })
        if self.reranking_enabled:
            for r in results:
                r["relevance"] = min(1.0, r["relevance"] * 1.1)
            results = sorted(results, key=lambda x: x["relevance"], reverse=True)
        results = results[:self.max_results]
        if self.cache_enabled and self.cache_size > 0:
            self.cache[query] = results
            max_entries = max(1, self.cache_size // 10)
            if len(self.cache) > max_entries:
                items = list(self.cache.items())
                for key, _ in items[:len(items) - max_entries]:
                    del self.cache[key]
        elif self.cache_enabled:
            self.cache[query] = results
        return results


# ============================================================
# FITNESS FUNCTION
# ============================================================

class FitnessFunction:
    def __init__(self):
        self.weights = {"latency": 0.30, "accuracy": 0.40, "cost": 0.20, "reliability": 0.10}

    def calculate(self, results: Dict) -> float:
        latency_score = 1 / (1 + results.get("latency", 1.0))
        accuracy_score = results.get("accuracy", 0.5)
        cost_score = 1 / (1 + results.get("cost", 1.0))
        reliability_score = results.get("reliability", 0.5)
        return (self.weights["latency"] * latency_score +
                self.weights["accuracy"] * accuracy_score +
                self.weights["cost"] * cost_score +
                self.weights["reliability"] * reliability_score)


# ============================================================
# BENCHMARK RUNNER
# ============================================================

ENVIRONMENTS = {
    "small": {"queries": 10, "sources": 5, "timeout": 5},
    "medium": {"queries": 50, "sources": 10, "timeout": 10},
    "large": {"queries": 100, "sources": 20, "timeout": 30}
}


class BenchmarkRunner:
    def __init__(self, fitness: FitnessFunction):
        self.fitness = fitness

    def run_multi_env_benchmark(self, allele_id: str, genome: Dict) -> Dict:
        scores = []
        env_results = {}
        for env_name, env_config in ENVIRONMENTS.items():
            engine = SearchEngine(genome, seed=hash(allele_id + env_name) % 10000)
            queries = self._generate_queries(env_config["queries"], env_config["sources"])
            results = {"latency": 0.0, "accuracy": 0.0, "cost": 0.0, "reliability": 0.0}
            successful = 0
            total_latency = 0.0
            total_accuracy = 0.0
            total_cost = 0.0
            for q in queries:
                try:
                    start = time.time()
                    result = engine.search(q["text"], q["sources"])
                    end = time.time()
                    successful += 1
                    total_latency += (end - start)
                    total_cost += 0.001 * len(q["sources"])
                    total_accuracy += result[0]["relevance"] if result else 0.5
                except:
                    pass
            if successful > 0:
                results = {
                    "latency": total_latency / successful,
                    "accuracy": total_accuracy / successful,
                    "cost": total_cost / successful,
                    "reliability": successful / len(queries)
                }
            fitness_score = self.fitness.calculate(results)
            scores.append(fitness_score)
            env_results[env_name] = {"fitness": fitness_score, **results}
        avg_fitness = sum(scores) / len(scores)
        stability = 1 - (max(scores) - min(scores)) / max(1, max(scores))
        return {"fitness": avg_fitness, "env_scores": env_results, "stability": stability}

    def _generate_queries(self, count: int, sources_per_query: int) -> List[Dict]:
        source_pool = ["wikipedia", "github", "stackoverflow", "news", "academic", "docs", "blog", "forum"]
        query_texts = [
            "how to implement search", "best search algorithm", "search optimization techniques",
            "parallel search performance", "cache strategies for search", "search relevance ranking",
            "fast search implementation", "search architecture patterns", "scalable search systems",
            "search with vectors", "search indexing methods", "distributed search systems"
        ]
        queries = []
        for _ in range(count):
            num_sources = min(sources_per_query, len(source_pool))
            sources = random.sample(source_pool, num_sources)
            queries.append({"text": random.choice(query_texts), "sources": sources})
        return queries


# ============================================================
# MAIN
# ============================================================

def main():
    # Champion genome from the successful run
    champion_genome = {
        "parallelism": 8,
        "reranking_enabled": True,
        "batch_size": 50,
        "timeout_seconds": 60,
        "cache_size": 100,
        "max_results": 10,
        "cache_enabled": True
    }

    print("🏆 MEOS V0.3 - Champion Replay")
    print("=" * 60)
    print(f"Genome: {champion_genome}")
    print(f"Running 100 evaluations...")
    print("-" * 60)

    fitness = FitnessFunction()
    runner = BenchmarkRunner(fitness)

    results = []
    for i in range(100):
        allele_id = f"replay_{i}"
        result = runner.run_multi_env_benchmark(allele_id, champion_genome)
        results.append(result["fitness"])

        if (i + 1) % 10 == 0:
            print(f"  Run {i+1:3d}: {result['fitness']:.4f}  (stability: {result['stability']:.4f})")

    mean = statistics.mean(results)
    median = statistics.median(results)
    std_dev = statistics.stdev(results) if len(results) > 1 else 0.0
    min_val = min(results)
    max_val = max(results)

    print("-" * 60)
    print("\n📊 CHAMPION REPLAY RESULTS")
    print("=" * 60)
    print(f"  Mean:   {mean:.4f}")
    print(f"  Median: {median:.4f}")
    print(f"  StdDev: {std_dev:.4f}")
    print(f"  Min:    {min_val:.4f}")
    print(f"  Max:    {max_val:.4f}")
    print(f"  N:      {len(results)}")
    print("=" * 60)

    if mean > 0.95 and std_dev < 0.01:
        print("✅ CHAMPION IS REAL AND STABLE")
        print(f"   The 0.9600 champion is genuine and reproducible.")
    elif mean > 0.93 and std_dev < 0.02:
        print("⚠️ CHAMPION IS REAL BUT SLIGHTLY NOISY")
        print(f"   The champion is real but shows some variance.")
    else:
        print("❌ CHAMPION IS UNSTABLE OR NOISY")
        print(f"   The champion may be a lucky run rather than a true optimum.")

    print("=" * 60)


if __name__ == "__main__":
    main()
