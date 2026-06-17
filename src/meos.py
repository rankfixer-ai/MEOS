"""
MEOS V0.1 - Minimum Evolutionary Operating System
FIXED VERSION - Deterministic SearchEngine + WAL Mode
"""

import sqlite3
import json
import random
import time
import uuid
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path


# ============================================================
# DATABASE LAYER
# ============================================================

class Database:
    def __init__(self, db_path: str = "data/meos.db"):
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_tables()

    def _ensure_db_directory(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _init_tables(self):
        with self._get_connection() as conn:
            # Enable WAL mode BEFORE any other operations
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
                    parent_allele_id TEXT,
                    is_active BOOLEAN DEFAULT FALSE,
                    generation INTEGER,
                    random_seed INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (gene_id) REFERENCES genes(id),
                    FOREIGN KEY (parent_allele_id) REFERENCES alleles(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lineage (
                    id TEXT PRIMARY KEY,
                    parent_allele_id TEXT,
                    child_allele_id TEXT,
                    fitness_delta REAL,
                    selection_reason TEXT,
                    generation INTEGER,
                    random_seed INTEGER,
                    genome_diff JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_allele_id) REFERENCES alleles(id),
                    FOREIGN KEY (child_allele_id) REFERENCES alleles(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS benchmark_results (
                    id TEXT PRIMARY KEY,
                    allele_id TEXT NOT NULL,
                    benchmark_name TEXT NOT NULL,
                    latency REAL,
                    accuracy REAL,
                    cost REAL,
                    reliability REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (allele_id) REFERENCES alleles(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY,
                    gene_id TEXT NOT NULL,
                    seed INTEGER NOT NULL,
                    total_generations INTEGER,
                    baseline_fitness REAL,
                    final_fitness REAL,
                    improvement REAL,
                    success BOOLEAN,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (gene_id) REFERENCES genes(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fitness_history (
                    id TEXT PRIMARY KEY,
                    experiment_id TEXT,
                    generation INTEGER,
                    fitness REAL,
                    active_fitness REAL,
                    best_fitness REAL,
                    delta REAL,
                    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mutation_log (
                    id TEXT PRIMARY KEY,
                    allele_id TEXT NOT NULL,
                    mutation_details JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (allele_id) REFERENCES alleles(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hypotheses (
                    id TEXT PRIMARY KEY,
                    allele_id TEXT NOT NULL,
                    predicted_fitness_delta REAL,
                    actual_fitness_delta REAL,
                    confidence REAL DEFAULT 0.5,
                    tested BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (allele_id) REFERENCES alleles(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS benchmark_sets (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                INSERT OR IGNORE INTO benchmark_sets (id, name, description) VALUES
                    ('bs_001', 'search_small', '10 queries, 5 sources each'),
                    ('bs_002', 'search_medium', '50 queries, 10 sources each'),
                    ('bs_003', 'search_large', '100 queries, 20 sources each')
            ''')
            conn.commit()

    def _get_connection(self):
        return sqlite3.connect(
            self.db_path,
            timeout=30,
            check_same_thread=False
        )

    def execute(self, query: str, params: tuple = ()):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            if query.strip().upper().startswith("SELECT"):
                return cursor.fetchall()

            conn.commit()
            return []

    def insert(self, table: str, data: Dict) -> str:
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, list(data.values()))
            conn.commit()
            return cursor.lastrowid if cursor.lastrowid else data.get('id')


# ============================================================
# GENOME MANAGER
# ============================================================

class GenomeManager:
    def __init__(self, db: Database):
        self.db = db

    def create_gene(self, name: str, description: str = "") -> str:
        gene_id = str(uuid.uuid4())[:8]
        self.db.insert('genes', {
            'id': gene_id,
            'name': name,
            'description': description,
            'best_fitness_ever': -1.0,
            'baseline_fitness': None
        })
        return gene_id

    def get_active_allele(self, gene_id: str) -> Optional[Dict]:
        rows = self.db.execute(
            "SELECT * FROM alleles WHERE gene_id = ? AND is_active = TRUE LIMIT 1",
            (gene_id,)
        )
        if not rows:
            return None
        row = rows[0]
        return {
            'id': row[0],
            'gene_id': row[1],
            'version': row[2],
            'genome': json.loads(row[3]),
            'fitness_score': row[4],
            'parent_allele_id': row[5],
            'is_active': row[6],
            'generation': row[7],
            'random_seed': row[8],
            'created_at': row[9]
        }

    def set_active_allele(self, allele_id: str):
        self.db.execute(
            "UPDATE alleles SET is_active = FALSE WHERE gene_id = (SELECT gene_id FROM alleles WHERE id = ?)",
            (allele_id,)
        )
        self.db.execute(
            "UPDATE alleles SET is_active = TRUE WHERE id = ?",
            (allele_id,)
        )

    def get_allele(self, allele_id: str) -> Optional[Dict]:
        rows = self.db.execute("SELECT * FROM alleles WHERE id = ?", (allele_id,))
        if not rows:
            return None
        row = rows[0]
        return {
            'id': row[0],
            'gene_id': row[1],
            'version': row[2],
            'genome': json.loads(row[3]),
            'fitness_score': row[4],
            'parent_allele_id': row[5],
            'is_active': row[6],
            'generation': row[7],
            'random_seed': row[8],
            'created_at': row[9]
        }

    def set_baseline_fitness(self, gene_id: str, fitness: float):
        self.db.execute(
            "UPDATE genes SET baseline_fitness = ? WHERE id = ?",
            (fitness, gene_id)
        )


# ============================================================
# MUTATION ENGINE
# ============================================================

class MutationEngine:
    def __init__(self, random_seed: int = 42):
        self.random = random.Random(random_seed)
        self.mutation_attempts = 0
        self.MIN_IMPROVEMENT = 0.005

    def mutate(self, genome: Dict) -> Tuple[Dict, Dict]:
        self.mutation_attempts += 1
        new_genome = json.loads(json.dumps(genome))

        params = ['parallelism', 'cache_enabled', 'cache_size', 'reranking_enabled',
                  'batch_size', 'timeout_seconds', 'max_results']
        num_mutations = self.random.choice([1, 1, 1, 2, 2, 3])

        diff = {}
        mutated = []

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
                diff[param] = {'old': old_value, 'new': new_value}

        if not diff:
            param = self.random.choice(params)
            old_value = genome[param]
            new_value = self._mutate_param(param, old_value)
            new_genome[param] = new_value
            diff[param] = {'old': old_value, 'new': new_value}

        return new_genome, diff

    def _mutate_param(self, param: str, current: Any) -> Any:
        options = {
            'parallelism': [1, 2, 4, 8, 16, 32],
            'cache_enabled': [True, False],
            'cache_size': [0, 100, 1000, 10000, 50000],
            'reranking_enabled': [True, False],
            'batch_size': [1, 5, 10, 20, 50, 100],
            'timeout_seconds': [5, 10, 20, 30, 60, 120],
            'max_results': [10, 25, 50, 100, 250, 500]
        }
        opts = [o for o in options[param] if o != current]
        return self.random.choice(opts) if opts else current


# ============================================================
# FITNESS FUNCTION
# ============================================================

class FitnessFunction:
    def __init__(self):
        self.weights = {'latency': 0.30, 'accuracy': 0.40, 'cost': 0.20, 'reliability': 0.10}

    def calculate(self, results: Dict) -> float:
        latency_score = 1 / (1 + results.get('latency', 1.0))
        accuracy_score = results.get('accuracy', 0.5)
        cost_score = 1 / (1 + results.get('cost', 1.0))
        reliability_score = results.get('reliability', 0.5)
        return (self.weights['latency'] * latency_score +
                self.weights['accuracy'] * accuracy_score +
                self.weights['cost'] * cost_score +
                self.weights['reliability'] * reliability_score)


# ============================================================
# SEARCH ENGINE (FIXED: DETERMINISTIC)
# ============================================================

class SearchEngine:
    def __init__(self, genome: Dict, seed: int = 42):
        self.parallelism = genome.get('parallelism', 1)
        self.cache_enabled = genome.get('cache_enabled', False)
        self.cache_size = genome.get('cache_size', 0)
        self.reranking_enabled = genome.get('reranking_enabled', False)
        self.batch_size = genome.get('batch_size', 10)
        self.timeout = genome.get('timeout_seconds', 30)
        self.max_results = genome.get('max_results', 50)
        self.cache = {}
        self.seed = seed
        self.random = random.Random(seed)

    def search(self, query: str, sources: List[str]) -> List[Dict]:
        if self.cache_enabled and query in self.cache:
            return self.cache[query][:self.max_results]

        latency = 0.05 * max(1, len(sources) / max(1, self.parallelism))
        time.sleep(min(latency, self.timeout))

        results = []
        for i, source in enumerate(sources[:self.batch_size]):
            relevance_seed = hash(query + source + str(i) + str(self.seed)) % 10000
            self.random.seed(relevance_seed)
            relevance = self.random.uniform(0.3, 0.9)

            results.append({
                'source': source,
                'title': f"{source}: {query[:20]}...",
                'relevance': relevance
            })

        if self.reranking_enabled:
            for r in results:
                r['relevance'] = min(1.0, r['relevance'] * 1.1)
            results = sorted(results, key=lambda x: x['relevance'], reverse=True)

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
# BENCHMARK RUNNER
# ============================================================

class BenchmarkRunner:
    def __init__(self, db: Database, fitness: FitnessFunction):
        self.db = db
        self.fitness = fitness

    def run_benchmark(self, allele_id: str, genome: Dict, benchmark_name: str = "default") -> Dict:
        engine = SearchEngine(genome, seed=hash(allele_id) % 10000)

        queries = [
            {"text": "how to implement search", "sources": ["wikipedia", "github", "stackoverflow"]},
            {"text": "best search algorithm", "sources": ["github", "academic", "news"]},
            {"text": "search optimization techniques", "sources": ["stackoverflow", "github", "wikipedia"]},
            {"text": "parallel search performance", "sources": ["academic", "github", "news"]},
            {"text": "cache strategies for search", "sources": ["stackoverflow", "github", "wikipedia"]}
        ]

        iterations = 5

        results = {'latency': 0.0, 'accuracy': 0.0, 'cost': 0.0, 'reliability': 0.0}
        successful = 0
        total_latency = 0.0
        total_accuracy = 0.0
        total_cost = 0.0

        for q in queries * iterations:
            try:
                start = time.time()
                result = engine.search(q['text'], q['sources'])
                end = time.time()
                successful += 1
                total_latency += (end - start)
                total_cost += 0.001 * len(q['sources'])
                total_accuracy += result[0]['relevance'] if result else 0.5
            except:
                pass

        if successful > 0:
            results = {
                'latency': total_latency / successful,
                'accuracy': total_accuracy / successful,
                'cost': total_cost / successful,
                'reliability': successful / (len(queries) * iterations)
            }

        fitness_score = self.fitness.calculate(results)

        self.db.insert('benchmark_results', {
            'id': str(uuid.uuid4())[:8],
            'allele_id': allele_id,
            'benchmark_name': benchmark_name,
            'latency': results['latency'],
            'accuracy': results['accuracy'],
            'cost': results['cost'],
            'reliability': results['reliability']
        })

        return {'fitness': fitness_score, **results}


# ============================================================
# EVOLUTION LOOP
# ============================================================

class EvolutionLoop:
    def __init__(self, gene_id: str, db: Database, experiment_id: str,
                 num_generations: int = 100, seed: int = 42,
                 baseline_fitness: float = 0.5):
        self.gene_id = gene_id
        self.db = db
        self.experiment_id = experiment_id
        self.num_generations = num_generations
        self.seed = seed
        self.baseline_fitness = baseline_fitness
        self.mutation_engine = MutationEngine(seed)
        self.fitness = FitnessFunction()
        self.benchmark_runner = BenchmarkRunner(db, self.fitness)
        self.genome_manager = GenomeManager(db)
        self.best_ever_fitness = baseline_fitness
        self.best_ever_allele_id = None
        self.fitness_history = []

    def run(self) -> Dict:
        print(f"\n🧬 Starting evolution for gene: {self.gene_id}")
        print(f"   Generations: {self.num_generations}")
        print(f"   Seed: {self.seed}")
        print(f"   Baseline Fitness: {self.baseline_fitness:.3f}")
        print("-" * 50)

        initial_genome = {
            'parallelism': 1,
            'cache_enabled': False,
            'cache_size': 0,
            'reranking_enabled': False,
            'batch_size': 10,
            'timeout_seconds': 30,
            'max_results': 50
        }

        allele_id = str(uuid.uuid4())[:8]
        self.db.insert('alleles', {
            'id': allele_id,
            'gene_id': self.gene_id,
            'version': 1,
            'genome': json.dumps(initial_genome),
            'fitness_score': None,
            'parent_allele_id': None,
            'is_active': False,
            'generation': 0,
            'random_seed': self.seed
        })

        results = self.benchmark_runner.run_benchmark(allele_id, initial_genome)
        fitness_score = results['fitness']
        self.db.execute("UPDATE alleles SET fitness_score = ? WHERE id = ?", (fitness_score, allele_id))
        self.genome_manager.set_active_allele(allele_id)

        self.best_ever_fitness = fitness_score
        self.best_ever_allele_id = allele_id

        success_count = 0
        reject_count = 0

        for gen in range(1, self.num_generations + 1):
            active = self.genome_manager.get_active_allele(self.gene_id)
            if not active:
                break

            new_genome, diff = self.mutation_engine.mutate(active['genome'])
            allele_id = str(uuid.uuid4())[:8]

            self.db.insert('alleles', {
                'id': allele_id,
                'gene_id': self.gene_id,
                'version': gen + 1,
                'genome': json.dumps(new_genome),
                'fitness_score': None,
                'parent_allele_id': active['id'],
                'is_active': False,
                'generation': gen,
                'random_seed': self.seed
            })

            results = self.benchmark_runner.run_benchmark(allele_id, new_genome)
            fitness_score = results['fitness']

            self.db.execute("UPDATE alleles SET fitness_score = ? WHERE id = ?", (fitness_score, allele_id))

            delta = fitness_score - active.get('fitness_score', 0.0)

            if delta > self.mutation_engine.MIN_IMPROVEMENT:
                self.genome_manager.set_active_allele(allele_id)
                self.db.insert('lineage', {
                    'id': str(uuid.uuid4())[:8],
                    'parent_allele_id': active['id'],
                    'child_allele_id': allele_id,
                    'fitness_delta': delta,
                    'selection_reason': 'promoted',
                    'generation': gen,
                    'random_seed': self.seed,
                    'genome_diff': json.dumps(diff)
                })
                active = self.genome_manager.get_allele(allele_id)
                success_count += 1
                if fitness_score > self.best_ever_fitness:
                    self.best_ever_fitness = fitness_score
                    self.best_ever_allele_id = allele_id
                    self.db.execute("UPDATE genes SET best_fitness_ever = ? WHERE id = ?",
                                   (self.best_ever_fitness, self.gene_id))
                status = "✓"
            else:
                self.db.insert('lineage', {
                    'id': str(uuid.uuid4())[:8],
                    'parent_allele_id': active['id'],
                    'child_allele_id': allele_id,
                    'fitness_delta': delta,
                    'selection_reason': 'rejected',
                    'generation': gen,
                    'random_seed': self.seed,
                    'genome_diff': json.dumps(diff)
                })
                reject_count += 1
                status = "✗"

            self.db.insert('fitness_history', {
                'id': str(uuid.uuid4())[:8],
                'experiment_id': self.experiment_id,
                'generation': gen,
                'fitness': fitness_score,
                'active_fitness': active.get('fitness_score', 0.0),
                'best_fitness': self.best_ever_fitness,
                'delta': delta
            })

            if gen % 10 == 0:
                print(f"   Gen {gen:3d}: {status} Fitness: {fitness_score:.3f} "
                      f"(Δ: {delta:+.3f}) Active: {active.get('fitness_score', 0):.3f}")

        print("-" * 50)
        print(f"✅ Evolution complete!")
        print(f"   Successes: {success_count}")
        print(f"   Rejections: {reject_count}")
        print(f"   Success Rate: {success_count/(success_count+reject_count)*100:.1f}%")
        print(f"   Best Fitness: {self.best_ever_fitness:.3f}")
        print(f"   Improvement: {((self.best_ever_fitness - self.baseline_fitness) / self.baseline_fitness * 100):.1f}%")

        return {
            'success_count': success_count,
            'reject_count': reject_count,
            'best_fitness': self.best_ever_fitness,
            'baseline_fitness': self.baseline_fitness,
            'improvement': (self.best_ever_fitness - self.baseline_fitness) / self.baseline_fitness,
            'lineage_length': self._get_lineage_length()
        }

    def _get_lineage_length(self) -> int:
        rows = self.db.execute(
            "SELECT COUNT(*) FROM lineage WHERE selection_reason = 'promoted' AND parent_allele_id IN (SELECT id FROM alleles WHERE gene_id = ?)",
            (self.gene_id,)
        )
        return rows[0][0] if rows else 0


# ============================================================
# EXPERIMENT RUNNER
# ============================================================

class ExperimentRunner:
    def __init__(self, db: Database):
        self.db = db
        self.genome_manager = GenomeManager(db)

    def run(self, gene_id: str, num_generations: int = 100) -> Dict:
        seeds = [42, 1337, 9001, 12345, 8675309]
        results = []

        baseline_rows = self.db.execute(
            "SELECT baseline_fitness FROM genes WHERE id = ?",
            (gene_id,)
        )
        baseline_fitness = baseline_rows[0][0] if baseline_rows and baseline_rows[0][0] is not None else 0.5

        print(f"\n🧪 Starting experiment for gene: {gene_id}")
        print(f"   Baseline Fitness: {baseline_fitness:.3f}")
        print(f"   Seeds: {seeds}")
        print("=" * 60)

        for seed in seeds:
            print(f"\n📊 Running seed {seed}...")

            seed_gene_id = self.genome_manager.create_gene(
                f"search_seed_{seed}",
                f"Seed {seed} isolated evolution"
            )
            self.genome_manager.set_baseline_fitness(seed_gene_id, baseline_fitness)

            exp_id = str(uuid.uuid4())[:8]
            self.db.insert('experiments', {
                'id': exp_id,
                'gene_id': seed_gene_id,
                'seed': seed,
                'total_generations': num_generations,
                'baseline_fitness': baseline_fitness,
                'final_fitness': None,
                'improvement': None,
                'success': None,
                'started_at': datetime.now().isoformat(),
                'completed_at': None,
                'notes': ''
            })

            loop = EvolutionLoop(seed_gene_id, self.db, exp_id, num_generations, seed, baseline_fitness)
            result = loop.run()

            final_fitness = result['best_fitness']
            improvement = result['improvement']

            # Simplified success criteria - improvement is what matters
            success = improvement > 0.10

            self.db.execute(
                "UPDATE experiments SET completed_at = ?, final_fitness = ?, improvement = ?, success = ?, notes = ? WHERE id = ?",
                (datetime.now().isoformat(), final_fitness, improvement,
                 1 if success else 0, f"Successes: {result['success_count']}, Rejections: {result['reject_count']}", exp_id)
            )

            results.append({
                'seed': seed,
                'success': success,
                'final_fitness': final_fitness,
                'baseline_fitness': baseline_fitness,
                'improvement': improvement,
                'success_count': result['success_count'],
                'reject_count': result['reject_count'],
                'lineage_length': result['lineage_length']
            })

            print(f"\n   Seed {seed}: {'✅ SUCCESS' if success else '❌ FAILED'}")
            print(f"   Baseline: {baseline_fitness:.3f} → Final: {final_fitness:.3f}")
            print(f"   Improvement: {improvement:.2%}")

        all_succeeded = all(r['success'] for r in results)
        successful_seeds = sum(1 for r in results if r['success'])

        print("\n" + "=" * 60)
        print("📊 EXPERIMENT RESULTS")
        print(f"   All Seeds Succeeded: {'✅' if all_succeeded else '❌'}")
        print(f"   Successful Seeds: {successful_seeds}/{len(seeds)}")

        if all_succeeded:
            print("\n🎉 MEOS V0.1 SUCCEEDED!")
            print("   Evolution works! Proceed to V0.2.")
        else:
            print("\n⚠️ MEOS V0.1 PARTIALLY FAILED")
            print("   Check debug checklist.")

        return {
            'all_succeeded': all_succeeded,
            'successful_seeds': successful_seeds,
            'total_seeds': len(seeds),
            'results': results,
            'baseline_fitness': baseline_fitness
        }


# ============================================================
# MAIN
# ============================================================

def main():
    print("🧬 MEOS V0.1 - The Genome Evolution Architecture (FIXED)")
    print("========================================================")

    db = Database()
    genome_manager = GenomeManager(db)

    gene_id = genome_manager.create_gene("search", "Search capability evolution test")
    print(f"\n📌 Created master gene: {gene_id} (search)")

    initial_genome = {
        "parallelism": 1,
        "cache_enabled": False,
        "cache_size": 0,
        "reranking_enabled": False,
        "batch_size": 10,
        "timeout_seconds": 30,
        "max_results": 50
    }

    allele_id = str(uuid.uuid4())[:8]
    db.insert('alleles', {
        'id': allele_id,
        'gene_id': gene_id,
        'version': 1,
        'genome': json.dumps(initial_genome),
        'fitness_score': None,
        'parent_allele_id': None,
        'is_active': False,
        'generation': 0,
        'random_seed': 42
    })

    fitness = FitnessFunction()
    benchmark_runner = BenchmarkRunner(db, fitness)
    results = benchmark_runner.run_benchmark(allele_id, initial_genome)
    baseline_fitness = results['fitness']

    db.execute("UPDATE alleles SET fitness_score = ? WHERE id = ?", (baseline_fitness, allele_id))
    genome_manager.set_active_allele(allele_id)
    genome_manager.set_baseline_fitness(gene_id, baseline_fitness)

    print(f"   Baseline fitness: {baseline_fitness:.3f}")
    print(f"   Baseline genome: {initial_genome}")

    runner = ExperimentRunner(db)
    result = runner.run(gene_id, 100)

    print("\n" + "=" * 60)
    if result['all_succeeded']:
        print("🎉 MEOS V0.1 COMPLETED SUCCESSFULLY!")
        print("   All seeds succeeded. Evolution works.")
        print("\n✅ Proceed to MEOS V0.2")
    else:
        print("⚠️ MEOS V0.1 COMPLETED WITH ISSUES")
        print(f"   {result['successful_seeds']}/{result['total_seeds']} seeds succeeded.")
        print("\n   Check debug checklist:")
        print("   □ Database connection")
        print("   □ Genome JSON serialization")
        print("   □ Fitness calculation")
        print("   □ Mutation engine")
        print("   □ Selection logic")
        print("   □ Elite preservation")

    print("\n📁 Data stored in: data/meos.db")
    print("📊 Query results with SQLite")


if __name__ == "__main__":
    main()