"""
MEOS V0.3 - Core Evolutionary Loop
Modular implementation with Selection Engine integration
"""

import sqlite3
import json
import random
import time
import uuid
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Import selection engine
import sys
sys.path.append(".")
from src.selection.selection_engine import SelectionEngine


# ============================================================
# DATABASE LAYER
# ============================================================

class Database:
    def __init__(self, db_path: str = "data/meos_v0.3.db"):
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_tables()

    def _ensure_db_directory(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _init_tables(self):
        with self._get_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.commit()
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS genes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    best_fitness_ever REAL DEFAULT -1,
                    baseline_fitness REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alleles (
                    id TEXT PRIMARY KEY,
                    gene_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    genome JSON NOT NULL,
                    fitness_score REAL,
                    stability_score REAL,
                    parent_allele_id TEXT,
                    is_active BOOLEAN DEFAULT FALSE,
                    generation INTEGER,
                    random_seed INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (gene_id) REFERENCES genes(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS experiment_runs (
                    id TEXT PRIMARY KEY,
                    seed INTEGER NOT NULL,
                    baseline_fitness REAL,
                    final_fitness REAL,
                    success INTEGER DEFAULT 0,
                    plateau_generation INTEGER,
                    total_generations INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mutation_trials (
                    id TEXT PRIMARY KEY,
                    parent_allele_id TEXT,
                    child_allele_id TEXT,
                    run_id TEXT NOT NULL,
                    seed INTEGER NOT NULL,
                    generation INTEGER NOT NULL,
                    fitness_before REAL,
                    fitness_after REAL,
                    stability_before REAL,
                    stability_after REAL,
                    accepted_parent_fitness REAL,
                    delta REAL,
                    parent_genome_hash TEXT,
                    child_genome_hash TEXT,
                    evaluation_result TEXT NOT NULL CHECK (
                        evaluation_result IN (
                            "PROMOTED",
                            "PROMOTED_SOFT",
                            "PROMOTED_CHAMPION",
                            "REJECTED_FITNESS",
                            "REJECTED_SOFT",
                            "REJECTED_STABILITY",
                            "REJECTED_GENERALIZATION",
                            "REJECTED_THRESHOLD"
                        )
                    ),
                    fitness_score REAL,
                    generalization_score REAL,
                    stability_score REAL,
                    environment_small REAL,
                    environment_medium REAL,
                    environment_large REAL,
                    combined_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES experiment_runs(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mutation_events (
                    id TEXT PRIMARY KEY,
                    trial_id TEXT NOT NULL,
                    parameter TEXT NOT NULL,
                    mutation_type TEXT NOT NULL CHECK (
                        mutation_type IN (
                            "toggle_boolean",
                            "increase_numeric",
                            "decrease_numeric",
                            "categorical_swap"
                        )
                    ),
                    mutation_order INTEGER NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    attributed_delta REAL,
                    FOREIGN KEY (trial_id) REFERENCES mutation_trials(id)
                )
            ''')

            cursor.execute('''
                CREATE VIEW IF NOT EXISTS promotion_audit AS
                SELECT 
                    mt.id as trial_id,
                    mt.run_id,
                    mt.seed,
                    mt.generation,
                    mt.fitness_before,
                    mt.fitness_after,
                    mt.delta,
                    mt.accepted_parent_fitness,
                    mt.evaluation_result,
                    mt.fitness_score,
                    mt.generalization_score,
                    mt.stability_score,
                    mt.environment_small,
                    mt.environment_medium,
                    mt.environment_large,
                    mt.combined_score,
                    me.parameter,
                    me.mutation_type,
                    me.mutation_order,
                    me.old_value,
                    me.new_value,
                    me.attributed_delta
                FROM mutation_trials mt
                JOIN mutation_events me ON mt.id = me.trial_id
                WHERE mt.evaluation_result IN ("PROMOTED", "PROMOTED_SOFT", "PROMOTED_CHAMPION")
            ''')

            cursor.execute('''
                CREATE VIEW IF NOT EXISTS gene_effects AS
                SELECT
                    me.parameter,
                    COUNT(*) AS count,
                    SUM(CASE WHEN me.attributed_delta > 0 THEN 1 ELSE 0 END) AS positive,
                    SUM(CASE WHEN me.attributed_delta < 0 THEN 1 ELSE 0 END) AS negative,
                    SUM(CASE WHEN me.attributed_delta = 0 THEN 1 ELSE 0 END) AS neutral,
                    AVG(me.attributed_delta) AS avg_delta,
                    SUM(me.attributed_delta) AS total_delta
                FROM mutation_events me
                GROUP BY me.parameter
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trials_run ON mutation_trials(run_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trials_generation ON mutation_trials(seed, generation)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trials_result ON mutation_trials(evaluation_result)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_trial ON mutation_events(trial_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_parameter ON mutation_events(parameter)')

            conn.commit()

    def _get_connection(self):
        return sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)

    def execute(self, query: str, params: tuple = ()):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            conn.commit()
            return []

    def insert(self, table: str, data: Dict) -> str:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, list(data.values()))
            conn.commit()
            return cursor.lastrowid if cursor.lastrowid else data.get("id")


# ============================================================
# MUTATION ENGINE
# ============================================================

class MutationEngine:
    def __init__(self, random_seed: int = 42):
        self.random = random.Random(random_seed)
        self.mutation_attempts = 0
        self._mutation_events = []

    @staticmethod
    def hash_genome(genome: Dict) -> str:
        return hashlib.md5(
            json.dumps(genome, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16]

    def mutate(self, genome: Dict, generation: int, current_fitness: float = None,
               no_improvement_counter: int = 0, stagnation_threshold: int = 5,
               champion_stagnation_counter: int = 0, champion_stagnation_threshold: int = 10) -> Tuple[Dict, Dict]:
        self.mutation_attempts += 1
        new_genome = json.loads(json.dumps(genome))

        params = ["parallelism", "cache_enabled", "cache_size", "reranking_enabled",
                  "batch_size", "timeout_seconds", "max_results",
                  "scoring_strategy", "retrieval_depth",
                  "cache_eviction_policy", "ranking_model_temp"]

        if current_fitness is not None and current_fitness > 0.85:
            if champion_stagnation_counter >= champion_stagnation_threshold:
                num_mutations = self.random.choice([3, 4, 5, 6, 7])
                mutation_mode = "champion_macro_jump"
            elif no_improvement_counter >= stagnation_threshold:
                num_mutations = self.random.choice([2, 3, 4, 5])
                mutation_mode = "macro_jump"
            else:
                num_mutations = self.random.choice([1, 1, 1, 1, 1, 1, 1, 1, 1, 2])
                mutation_mode = "fine_tune"
        else:
            num_mutations = self.random.choice([1, 1, 1, 2, 2, 3])
            mutation_mode = "explore"

        diff = {}
        mutated = []
        self._mutation_events = []
        event_order = 0

        for _ in range(num_mutations):
            available = [p for p in params if p not in mutated]
            if not available:
                break
            param = self.random.choice(available)
            mutated.append(param)
            old_value = genome[param]
            new_value = self._mutate_param(param, old_value)
            if new_value != old_value:
                new_genome[param] = new_value
                diff[param] = {"old": old_value, "new": new_value}
                self._mutation_events.append({
                    "parameter": param,
                    "mutation_type": self._get_mutation_type(param, old_value, new_value),
                    "mutation_order": event_order,
                    "old_value": str(old_value),
                    "new_value": str(new_value),
                    "mutation_mode": mutation_mode
                })
                event_order += 1

        if not diff:
            param = self.random.choice(params)
            old_value = genome[param]
            new_value = self._mutate_param(param, old_value)
            new_genome[param] = new_value
            diff[param] = {"old": old_value, "new": new_value}
            self._mutation_events.append({
                "parameter": param,
                "mutation_type": self._get_mutation_type(param, old_value, new_value),
                "mutation_order": 0,
                "old_value": str(old_value),
                "new_value": str(new_value),
                "mutation_mode": mutation_mode
            })

        return new_genome, diff

    def _mutate_param(self, param: str, current: Any) -> Any:
        options = {
            "parallelism": [4, 8, 12, 16],
            "cache_enabled": [True, False],
            "cache_size": [0, 100, 500, 1000, 5000],
            "reranking_enabled": [True, False],
            "batch_size": [30, 40, 50, 60, 75],
            "timeout_seconds": [45, 50, 60, 70, 75],
            "max_results": [5, 10, 15, 20],
            "scoring_strategy": ["cosine", "dot", "euclidean"],
            "retrieval_depth": [3, 5, 10, 20],
            "cache_eviction_policy": ["lru", "lfu", "fifo"],
            "ranking_model_temp": [0.1, 0.3, 0.5, 0.7, 1.0]
        }
        opts = [o for o in options[param] if o != current]
        return self.random.choice(opts) if opts else current

    def _get_mutation_type(self, param: str, old_value: Any, new_value: Any) -> str:
        if isinstance(old_value, bool):
            return "toggle_boolean"
        elif isinstance(old_value, (int, float)):
            if new_value > old_value:
                return "increase_numeric"
            elif new_value < old_value:
                return "decrease_numeric"
        return "categorical_swap"

    def get_mutation_events(self) -> List[Dict]:
        return self._mutation_events


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
        self.scoring_strategy = genome.get("scoring_strategy", "cosine")
        self.retrieval_depth = genome.get("retrieval_depth", 10)
        self.cache_eviction_policy = genome.get("cache_eviction_policy", "lru")
        self.ranking_model_temp = genome.get("ranking_model_temp", 0.5)
        self.seed = seed
        self.random = random.Random(seed)
        self.cache = {}

    def search(self, query: str, sources: List[str]) -> List[Dict]:
        if self.cache_enabled and query in self.cache:
            return self.cache[query][:self.max_results]
        latency = 0.05 * max(1, len(sources) / max(1, self.parallelism))
        pass  # time.sleep removed for determinism
        results = []
        for i, source in enumerate(sources[:self.batch_size]):
            self.random.seed(int(hashlib.md5((query + source + str(i) + str(self.seed)).encode()).hexdigest(), 16) % 10000)
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

    def run_multi_env_benchmark(self, allele_id: str, genome: Dict, gen_seed: int = 42) -> Dict:
        scores = []
        env_results = {}
        for env_index, (env_name, env_config) in enumerate(ENVIRONMENTS.items()):
            engine = SearchEngine(genome, seed=int(hashlib.md5((json.dumps(genome, sort_keys=True) + env_name).encode()).hexdigest(), 16) % 10000)
            queries = self._generate_queries(env_config["queries"], env_config["sources"], gen_seed + env_index)
            results = {"latency": 0.0, "accuracy": 0.0, "cost": 0.0, "reliability": 0.0}
            successful = 0
            total_latency = 0.0
            total_accuracy = 0.0
            total_cost = 0.0
            for q in queries:
                try:
                    result = engine.search(q["text"], q["sources"])
                    successful += 1
                    total_latency += 0.05 * max(1, len(q["sources"]) / max(1, genome.get("parallelism", 1)))
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

    def _generate_queries(self, count: int, sources_per_query: int, seed: int = 42) -> List[Dict]:
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
            sources = random.Random(seed).sample(source_pool, num_sources)
            queries.append({"text": random.Random(seed).choice(query_texts), "sources": sources})
        return queries


# ============================================================
# EVOLUTION LOOP
# ============================================================

class EvolutionLoop:
    def __init__(self, gene_id: str, db: Database, experiment_id: str,
                 num_generations: int = 100, seed: int = 42,
                 baseline_fitness: float = 0.5, plateau_generations: int = 10,
                 initial_allele_id: str = None, initial_genome: Dict = None,
                 selector: SelectionEngine = None):
        self.gene_id = gene_id
        self.db = db
        self.experiment_id = experiment_id
        self.num_generations = num_generations
        self.seed = seed
        self.baseline_fitness = baseline_fitness
        self.plateau_generations = plateau_generations
        self.mutation_engine = MutationEngine(seed)
        self.fitness = FitnessFunction()
        self.benchmark_runner = BenchmarkRunner(self.fitness)
        self.selector = selector or SelectionEngine(target_threshold=0.89)
        self.best_ever_fitness = baseline_fitness
        self.best_ever_genome = initial_genome.copy() if initial_genome else None
        self.best_ever_allele_id = initial_allele_id
        self.no_improvement_counter = 0
        self.stagnation_threshold = 5
        self.champion_stagnation_counter = 0
        self.champion_stagnation_threshold = 10
        self.elite_archive = []
        self.max_elite_size = 10

    def _get_active_allele(self) -> Optional[Dict]:
        rows = self.db.execute("SELECT * FROM alleles WHERE gene_id = ? AND is_active = TRUE LIMIT 1", (self.gene_id,))
        if not rows:
            return None
        row = rows[0]
        return {
            "id": row[0], "gene_id": row[1], "version": row[2],
            "genome": json.loads(row[3]), "fitness_score": row[4],
            "stability_score": float(row[5]) if len(row) > 5 and row[5] is not None else 0.0,
            "parent_allele_id": row[6] if len(row) > 6 else None,
            "is_active": row[7] if len(row) > 7 else False,
            "generation": row[8] if len(row) > 8 else 0,
            "random_seed": row[9] if len(row) > 9 else 0
        }

    def _set_active_allele(self, allele_id: str, reason: str = ""):
        old_active = self._get_active_allele()
        old_fitness = old_active["fitness_score"] if old_active else 0.0
        new_allele = self._get_allele(allele_id)
        new_fitness = new_allele["fitness_score"] if new_allele else 0.0
        self.db.execute("UPDATE alleles SET is_active = FALSE WHERE gene_id = (SELECT gene_id FROM alleles WHERE id = ?)", (allele_id,))
        self.db.execute("UPDATE alleles SET is_active = TRUE WHERE id = ?", (allele_id,))
        if old_active:
            print(f"   [SWITCH] {old_active['id'][:8]}->{allele_id[:8]} | {old_fitness:.4f}->{new_fitness:.4f} | {reason}")

    def _get_allele(self, allele_id: str) -> Optional[Dict]:
        rows = self.db.execute("SELECT * FROM alleles WHERE id = ?", (allele_id,))
        if not rows:
            return None
        row = rows[0]
        return {
            "id": row[0], "gene_id": row[1], "version": row[2],
            "genome": json.loads(row[3]), "fitness_score": row[4],
            "stability_score": float(row[5]) if len(row) > 5 and row[5] is not None else 0.0,
            "parent_allele_id": row[6] if len(row) > 6 else None,
            "is_active": row[7] if len(row) > 7 else False,
            "generation": row[8] if len(row) > 8 else 0,
            "random_seed": row[9] if len(row) > 9 else 0
        }

    def run(self) -> Dict:
        print(f"\nStarting evolution for seed: {self.seed}")
        print(f"   Generations: {self.num_generations}")
        print(f"   Baseline Fitness: {self.baseline_fitness:.3f}")
        print("-" * 50)

        initial_genome = {"parallelism": 1, "cache_enabled": False, "cache_size": 0,
                          "reranking_enabled": False, "batch_size": 10,
                          "timeout_seconds": 30, "max_results": 50,
                          "scoring_strategy": "cosine", "retrieval_depth": 10,
                          "cache_eviction_policy": "lru", "ranking_model_temp": 0.5}

        allele_id = str(uuid.uuid4())[:8]
        self.db.insert("alleles", {
            "id": allele_id, "gene_id": self.gene_id, "version": 1,
            "genome": json.dumps(initial_genome), "fitness_score": None,
            "stability_score": None,
            "parent_allele_id": None, "is_active": False, "generation": 0,
            "random_seed": self.seed
        })

        results = self.benchmark_runner.run_multi_env_benchmark(allele_id, initial_genome)
        fitness_score = results["fitness"]
        stability_score = results["stability"]
        self.db.execute("UPDATE alleles SET fitness_score = ? WHERE id = ?", (fitness_score, allele_id))
        self.db.execute("UPDATE alleles SET stability_score = ? WHERE id = ?", (stability_score, allele_id))
        self._set_active_allele(allele_id, "baseline")

        self.best_ever_fitness = fitness_score
        self.best_ever_allele_id = allele_id
        self.best_ever_genome = initial_genome.copy()

        success_count = 0
        reject_count = 0
        generations_since_improvement = 0
        stopped_early = False
        final_gen = self.num_generations

        for gen in range(1, self.num_generations + 1):
            active = self._get_active_allele()
            if not active:
                break

            parent_fitness = active.get("fitness_score", 0.0)
            parent_stability = active.get("stability_score", 0.0)
            # V0.4: Stagnation-aware parent selection
            if hasattr(self, "elite_archive") and self.elite_archive:
                if self.no_improvement_counter >= 15:
                    alt_elites = [e for e in self.elite_archive if e['fitness'] < self.best_ever_fitness * 0.995]
                    if alt_elites:
                        parent_genome = self.mutation_engine.random.choice(alt_elites)['genome']
                    else:
                        parent_genome = self.mutation_engine.random.choice(self.elite_archive)['genome']
                elif self.no_improvement_counter >= 3:
                    parent_genome = self.mutation_engine.random.choice(self.elite_archive)['genome']
                elif self.mutation_engine.random.random() < 0.3:
                    parent_genome = self.mutation_engine.random.choice(self.elite_archive)['genome']
                else:
                    parent_genome = self.best_ever_genome if self.best_ever_genome else initial_genome
            else:
                parent_genome = self.best_ever_genome if self.best_ever_genome else initial_genome

            new_genome, diff = self.mutation_engine.mutate(
                parent_genome, gen, parent_fitness,
                self.no_improvement_counter, self.stagnation_threshold,
                self.champion_stagnation_counter, self.champion_stagnation_threshold
            )
            allele_id = str(uuid.uuid4())[:8]

            self.db.insert("alleles", {
                "id": allele_id, "gene_id": self.gene_id, "version": gen + 1,
                "genome": json.dumps(new_genome), "fitness_score": None,
                "stability_score": None,
                "parent_allele_id": active["id"], "is_active": False,
                "generation": gen, "random_seed": self.seed
            })

            results = self.benchmark_runner.run_multi_env_benchmark(allele_id, new_genome, gen)
            fitness_score = results["fitness"]
            stability_score = results["stability"]
            env_scores = {env: v['fitness'] for env, v in results['env_scores'].items()}
            generalization_score = sum(env_scores.values()) / len(env_scores)

            self.db.execute("UPDATE alleles SET fitness_score = ? WHERE id = ?", (fitness_score, allele_id))
            self.db.execute("UPDATE alleles SET stability_score = ? WHERE id = ?", (stability_score, allele_id))

            delta_fitness = fitness_score - parent_fitness

            import random
            fitness_delta = fitness_score - self.best_ever_fitness

            if fitness_score > self.best_ever_fitness:
                accepted = True
                evaluation_result = "PROMOTED_CHAMPION"
                self.best_ever_fitness = fitness_score
                self.best_ever_genome = new_genome.copy()
                self.best_ever_allele_id = allele_id
                self.champion_stagnation_counter = 0
                self.no_improvement_counter = 0
                print(f"   NEW CHAMPION: {fitness_score:.4f}")
            elif stability_score > 0.98 and fitness_delta > -0.005:
                if random.Random(hashlib.md5(f'{self.seed}:{gen}:soft'.encode()).hexdigest()[:8]).random() < 0.25:
                    accepted = True
                    evaluation_result = "PROMOTED_SOFT"
                    print(f"   SOFT PROMOTED: {fitness_score:.4f} (stability: {stability_score:.4f})")
                else:
                    accepted = False
                    evaluation_result = "REJECTED_SOFT"
            else:
                accepted, evaluation_result = self.selector.evaluate_candidate(
                    parent_fitness, parent_stability,
                    fitness_score, stability_score
                )

            parent_hash = MutationEngine.hash_genome(parent_genome)
            child_hash = MutationEngine.hash_genome(new_genome)

            mutation_count = len(self.mutation_engine.get_mutation_events())
            attributed_delta = delta_fitness / mutation_count if mutation_count > 0 else 0

            trial_id = uuid.uuid4().hex

            print(f"[GEN {gen:3d}] parent={parent_fitness:>8.4f} candidate={fitness_score:>8.4f} champion={self.best_ever_fitness:>8.4f} | stability={stability_score:>8.4f} | {evaluation_result}")

            self.db.insert("mutation_trials", {
                "id": trial_id,
                "parent_allele_id": active["id"],
                "child_allele_id": allele_id,
                "run_id": self.experiment_id,
                "seed": self.seed,
                "generation": gen,
                "fitness_before": parent_fitness,
                "fitness_after": fitness_score,
                "stability_before": parent_stability,
                "stability_after": stability_score,
                "accepted_parent_fitness": self.best_ever_fitness,
                "delta": delta_fitness,
                "parent_genome_hash": parent_hash,
                "child_genome_hash": child_hash,
                "evaluation_result": evaluation_result,
                "fitness_score": fitness_score,
                "generalization_score": generalization_score,
                "stability_score": stability_score,
                "environment_small": env_scores.get('small'),
                "environment_medium": env_scores.get('medium'),
                "environment_large": env_scores.get('large'),
                "combined_score": self.selector.calculate_combined_score(fitness_score, stability_score)
            })

            for event in self.mutation_engine.get_mutation_events():
                self.db.insert("mutation_events", {
                    "id": uuid.uuid4().hex,
                    "trial_id": trial_id,
                    "parameter": event["parameter"],
                    "mutation_type": event["mutation_type"],
                    "mutation_order": event["mutation_order"],
                    "old_value": event["old_value"],
                    "new_value": event["new_value"],
                    "attributed_delta": attributed_delta
                })

            if accepted:
                self._set_active_allele(allele_id, evaluation_result)
                success_count += 1
                generations_since_improvement = 0
                self.no_improvement_counter = 0
                status = "?"
            else:
                reject_count += 1
                generations_since_improvement += 1
                self.no_improvement_counter += 1
                if self.no_improvement_counter >= 15 and self.elite_archive and len(self.elite_archive) >= 3:
                    print(f"   [V0.4.3] {self.no_improvement_counter} gens without improvement. Switching to archive parent.")
                    self.no_improvement_counter = 0
                self.champion_stagnation_counter += 1
                status = "?"

            if gen % 10 == 0:
                print(f"   Gen {gen:3d}: {status} Fitness: {fitness_score:.3f} "
                      f"(Delta: {delta_fitness:+.3f}) Active: {parent_fitness:.3f} "
                      f"Stability: {stability_score:.3f} | Result: {evaluation_result}")
                # P4: Archive diversity check
                top_alleles = self.db.execute(
                    "SELECT fitness_score, stability_score, genome FROM alleles WHERE gene_id = ? AND fitness_score IS NOT NULL ORDER BY fitness_score DESC LIMIT 10",
                    (self.gene_id,)
                )
                if len(top_alleles) >= 3:
                    fitnesses = [float(a[0]) for a in top_alleles if a[0] is not None]
                    if max(fitnesses) - min(fitnesses) < 0.005:
                        print(f"   [ARCHIVE] Low diversity: top10 spread={max(fitnesses)-min(fitnesses):.4f}")

            current_parent = self._get_active_allele()
            parent_stability = current_parent.get("stability_score", 0) if current_parent else 0
            if generations_since_improvement >= self.plateau_generations and parent_stability < 0.98:
                print(f"\n   Plateau detected at generation {gen}")
                stopped_early = True
                final_gen = gen
                break

        print("-" * 50)
        print(f"Evolution complete!")
        print(f"   Successes: {success_count}")
        print(f"   Rejections: {reject_count}")
        print(f"   Best Fitness: {self.best_ever_fitness:.4f}")
        print(f"   Improvement: {((self.best_ever_fitness - self.baseline_fitness) / self.baseline_fitness * 100):.1f}%")

        return {
            "success_count": success_count,
            "reject_count": reject_count,
            "best_fitness": self.best_ever_fitness,
            "baseline_fitness": self.baseline_fitness,
            "improvement": (self.best_ever_fitness - self.baseline_fitness) / self.baseline_fitness,
            "stopped_early": stopped_early,
            "final_generation": final_gen
        }


# ============================================================
# ENTRY POINT
# ============================================================

def run_evolutionary_loop(seed: int, generations: int, selector: SelectionEngine, db_name: str = "meos_v0.3.db",
                          seed_genome: str = None, debug: bool = False):
    """Main entry point for the evolutionary loop."""
    if debug:
        print("DEBUG: Entered run_evolutionary_loop")

    db = Database()
    if debug:
        print("DEBUG: Database initialized")

    gene_id = str(uuid.uuid4())[:8]
    db.insert("genes", {
        "id": gene_id,
        "name": "search",
        "description": "Search capability evolution",
        "best_fitness_ever": -1.0,
        "baseline_fitness": None
    })
    if debug:
        print(f"DEBUG: Gene created: {gene_id}")

    if seed_genome:
        initial_genome = json.loads(seed_genome)
        print(f"   Seeded with champion genome")
    else:
        initial_genome = {"parallelism": 1, "cache_enabled": False, "cache_size": 0,
                          "reranking_enabled": False, "batch_size": 10,
                          "timeout_seconds": 30, "max_results": 50,
                          "scoring_strategy": "cosine", "retrieval_depth": 10,
                          "cache_eviction_policy": "lru", "ranking_model_temp": 0.5}

    if debug:
        print("DEBUG: Creating initial allele")
    allele_id = str(uuid.uuid4())[:8]
    db.insert("alleles", {
        "id": allele_id, "gene_id": gene_id, "version": 1,
        "genome": json.dumps(initial_genome), "fitness_score": None,
        "stability_score": None,
        "parent_allele_id": None, "is_active": False, "generation": 0,
        "random_seed": seed
    })

    fitness = FitnessFunction()
    benchmark_runner = BenchmarkRunner(fitness)

    if debug:
        print("DEBUG: Running initial benchmark")
    results = benchmark_runner.run_multi_env_benchmark(allele_id, initial_genome, 0)
    baseline_fitness = results["fitness"]
    baseline_stability = results["stability"]
    db.execute("UPDATE alleles SET fitness_score = ? WHERE id = ?", (baseline_fitness, allele_id))
    db.execute("UPDATE alleles SET stability_score = ? WHERE id = ?", (baseline_stability, allele_id))
    db.execute("UPDATE alleles SET is_active = TRUE WHERE id = ?", (allele_id,))
    db.execute("UPDATE genes SET baseline_fitness = ? WHERE id = ?", (baseline_fitness, gene_id))

    print(f"\nGene: {gene_id}")
    print(f"   Baseline fitness: {baseline_fitness:.3f}")
    print(f"   Baseline stability: {baseline_stability:.3f}")
    print(f"   Seed: {seed}")
    print(f"   Generations: {generations}")

    run_id = uuid.uuid4().hex
    db.insert("experiment_runs", {
        "id": run_id,
        "seed": seed,
        "baseline_fitness": baseline_fitness,
        "final_fitness": None,
        "success": 0,
        "plateau_generation": None,
        "total_generations": generations
    })

    loop = EvolutionLoop(gene_id, db, run_id, generations, seed, baseline_fitness,
                         initial_allele_id=allele_id, initial_genome=initial_genome,
                         selector=selector)
    result = loop.run()

    success = result["best_fitness"] > 0.95
    db.execute(
        "UPDATE experiment_runs SET final_fitness = ?, success = ?, plateau_generation = ? WHERE id = ?",
        (result["best_fitness"], 1 if success else 0, result["final_generation"], run_id)
    )

    print("\n" + "=" * 60)
    if success:
        print("Experiment succeeded!")
    else:
        print("Experiment failed.")
    print(f"   Best Fitness: {result['best_fitness']:.4f}")
    print(f"   Improvement: {result['improvement']:.2%}")

    # Ensure database is initialized
    if debug:
        print("DEBUG: Creating EvolutionLoop")
    
    loop = EvolutionLoop(
        gene_id=gene_id,
        db=db,
        experiment_id=run_id,
        num_generations=generations,
        seed=seed,
        baseline_fitness=baseline_fitness,
        initial_allele_id=allele_id,
        initial_genome=initial_genome,
        selector=selector
    )
    
    return loop.run()

if __name__ == "__main__":
    # This block allows direct testing
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--generations", type=int, default=100)
    parser.add_argument("--threshold", type=float, default=0.89)
    args = parser.parse_args()
    
    from src.selection.selection_engine import SelectionEngine
    selector = SelectionEngine(target_threshold=args.threshold)
    
    run_evolutionary_loop(args.seed, args.generations, selector)
# Your new code goes here
def new_feature_function():
    print("Feature added via CLI!")
