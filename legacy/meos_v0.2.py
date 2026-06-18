"""
MEOS V0.2 - Multi-Environment Evolutionary System
Tests whether evolved genomes generalize across changing environments.
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
from collections import defaultdict


# ============================================================
# ENVIRONMENTS
# ============================================================

ENVIRONMENTS = {
    'small': {
        'queries': 10,
        'sources': 5,
        'timeout': 5,
        'description': 'Favors low latency'
    },
    'medium': {
        'queries': 50,
        'sources': 10,
        'timeout': 10,
        'description': 'Favors accuracy'
    },
    'large': {
        'queries': 100,
        'sources': 20,
        'timeout': 30,
        'description': 'Favors cache efficiency and parallelism'
    }
}


# ============================================================
# DATABASE LAYER (with WAL mode and timeout)
# ============================================================

class Database:
    def __init__(self, db_path: str = "data/meos_v0.2.db"):
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
            
            # Genes table
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
            
            # Alleles table
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
            
            # Lineage table
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
            
            # Environment benchmark results
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS env_benchmark_results (
                    id TEXT PRIMARY KEY,
                    allele_id TEXT NOT NULL,
                    env_name TEXT NOT NULL,
                    latency REAL,
                    accuracy REAL,
                    cost REAL,
                    reliability REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (allele_id) REFERENCES alleles(id)
                )
            ''')
            
            # Experiments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY,
                    gene_id TEXT NOT NULL,
                    seed INTEGER NOT NULL,
                    total_generations INTEGER,
                    baseline_fitness REAL,
                    final_fitness REAL,
                    improvement REAL,
                    stability REAL,
                    generalization_score REAL,
                    success BOOLEAN,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (gene_id) REFERENCES genes(id)
                )
            ''')
            
            # Fitness history
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
            
            # Mutation log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mutation_log (
                    id TEXT PRIMARY KEY,
                    allele_id TEXT NOT NULL,
                    mutation_details JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (allele_id) REFERENCES alleles(id)
                )
            ''')
            
            # NEW: Parameter attribution table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gene_effects (
                    id TEXT PRIMARY KEY,
                    parameter_name TEXT NOT NULL,
                    mutation_count INTEGER DEFAULT 0,
                    positive_count INTEGER DEFAULT 0,
                    negative_count INTEGER DEFAULT 0,
                    avg_delta REAL DEFAULT 0,
                    best_delta REAL DEFAULT 0,
                    worst_delta REAL DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
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
        self._gene_effects = defaultdict(lambda: {
            'positive': 0, 'negative': 0, 'total_delta': 0, 'count': 0
        })

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

    def record_effect(self, param: str, delta: float):
        """Record the effect of a mutation for parameter attribution."""
        if param not in self._gene_effects:
            self._gene_effects[param] = {'positive': 0, 'negative': 0, 'total_delta': 0, 'count': 0}
        
        self._gene_effects[param]['count'] += 1
        self._gene_effects[param]['total_delta'] += delta
        if delta > 0:
            self._gene_effects[param]['positive'] += 1
        else:
            self._gene_effects[param]['negative'] += 1

    def get_gene_effects(self) -> Dict:
        """Get aggregated gene effect data."""
        result = {}
        for param, data in self._gene_effects.items():
            if data['count'] > 0:
                result[param] = {
                    'avg_delta': data['total_delta'] / data['count'],
                    'positive_rate': data['positive'] / data['count'],
                    'negative_rate': data['negative'] / data['count'],
                    'count': data['count']
                }
        return result


# ============================================================
# FITNESS FUNCTION (Multi-Environment)
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
# SEARCH ENGINE (Multi-Environment Compatible)
# ============================================================

class SearchEngine:
    def __init__(self, genome: Dict, seed: int = 42, environment: Dict = None):
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
        
        # Environment-specific settings
        self.env = environment or {}

    def search(self, query: str, sources: List[str]) -> List[Dict]:
        if self.cache_enabled and query in self.cache:
            return self.cache[query][:self.max_results]

        # Use environment-specific timeout
        timeout = self.env.get('timeout', self.timeout)
        
        latency = 0.05 * max(1, len(sources) / max(1, self.parallelism))
        time.sleep(min(latency, timeout))

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
# BENCHMARK RUNNER (Multi-Environment)
# ============================================================

class BenchmarkRunner:
    def __init__(self, db: Database, fitness: FitnessFunction):
        self.db = db
        self.fitness = fitness

    def run_benchmark(self, allele_id: str, genome: Dict, env_name: str = "default") -> Dict:
        """Run benchmark in a specific environment."""
        env_config = ENVIRONMENTS.get(env_name, ENVIRONMENTS['medium'])
        
        engine = SearchEngine(genome, seed=hash(allele_id + env_name) % 10000, environment=env_config)

        # Use environment-specific query generation
        num_queries = env_config.get('queries', 50)
        num_sources = env_config.get('sources', 10)
        
        queries = self._generate_queries(num_queries, num_sources)

        results = {'latency': 0.0, 'accuracy': 0.0, 'cost': 0.0, 'reliability': 0.0}
        successful = 0
        total_latency = 0.0
        total_accuracy = 0.0
        total_cost = 0.0

        for q in queries:
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
                'reliability': successful / len(queries)
            }

        fitness_score = self.fitness.calculate(results)

        # Store environment-specific results
        self.db.insert('env_benchmark_results', {
            'id': str(uuid.uuid4())[:8],
            'allele_id': allele_id,
            'env_name': env_name,
            'latency': results['latency'],
            'accuracy': results['accuracy'],
            'cost': results['cost'],
            'reliability': results['reliability']
        })

        return {'fitness': fitness_score, **results}

    def run_multi_env_benchmark(self, allele_id: str, genome: Dict) -> Dict:
        """Run benchmark across all environments and return average fitness."""
        scores = []
        env_results = {}
        
        for env_name in ENVIRONMENTS.keys():
            result = self.run_benchmark(allele_id, genome, env_name)
            scores.append(result['fitness'])
            env_results[env_name] = result
        
        avg_fitness = sum(scores) / len(scores)
        
        return {
            'fitness': avg_fitness,
            'env_scores': env_results,
            'stability': 1 - (max(scores) - min(scores)) / max(1, max(scores))
        }

    def _generate_queries(self, count: int, sources_per_query: int) -> List[Dict]:
        """Generate test queries for a specific environment."""
        import random
        queries = []
        source_pool = ['wikipedia', 'github', 'stackoverflow', 'news', 'academic', 'docs', 'blog', 'forum']
        
        query_texts = [
            "how to implement search",
            "best search algorithm",
            "search optimization techniques",
            "parallel search performance",
            "cache strategies for search",
            "search relevance ranking",
            "fast search implementation",
            "search architecture patterns",
            "scalable search systems",
            "search with vectors",
            "search indexing methods",
            "distributed search systems"
        ]
        
        for _ in range(count):
            num_sources = min(sources_per_query, len(source_pool))
            sources = random.sample(source_pool, num_sources)
            queries.append({
                'text': random.choice(query_texts),
                'sources': sources
            })
        
        return queries


# ============================================================
# EVOLUTION LOOP (with Plateau Detection)
# ============================================================

class EvolutionLoop:
    def __init__(self, gene_id: str, db: Database, experiment_id: str,
                 num_generations: int = 100, seed: int = 42,
                 baseline_fitness: float = 0.5, plateau_generations: int = 10):
        self.gene_id = gene_id
        self.db = db
        self.experiment_id = experiment_id
        self.num_generations = num_generations
        self.seed = seed
        self.baseline_fitness = baseline_fitness
        self.plateau_generations = plateau_generations
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
        print(f"   Plateau Detection: {self.plateau_generations} generations")
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

        # Multi-environment benchmark for initial fitness
        results = self.benchmark_runner.run_multi_env_benchmark(allele_id, initial_genome)
        fitness_score = results['fitness']
        self.db.execute("UPDATE alleles SET fitness_score = ? WHERE id = ?", (fitness_score, allele_id))
        self.genome_manager.set_active_allele(allele_id)

        self.best_ever_fitness = fitness_score
        self.best_ever_allele_id = allele_id

        success_count = 0
        reject_count = 0
        generations_since_improvement = 0
        stopped_early = False

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

            # Multi-environment evaluation
            results = self.benchmark_runner.run_multi_env_benchmark(allele_id, new_genome)
            fitness_score = results['fitness']
            stability_score = results['stability']

            self.db.execute("UPDATE alleles SET fitness_score = ? WHERE id = ?", (fitness_score, allele_id))

            delta = fitness_score - active.get('fitness_score', 0.0)

            if delta > self.mutation_engine.MIN_IMPROVEMENT:
                # Record gene effect for each mutated parameter
                for param in diff.keys():
                    self.mutation_engine.record_effect(param, delta)
                
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
                generations_since_improvement = 0
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
                generations_since_improvement += 1
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
                      f"(Δ: {delta:+.3f}) Active: {active.get('fitness_score', 0):.3f} "
                      f"Stability: {results['stability']:.3f}")

            # Plateau detection - early stop
            if generations_since_improvement >= self.plateau_generations:
                print(f"\n   ⏹️ Plateau detected at generation {gen} "
                      f"(no improvement for {self.plateau_generations} generations)")
                stopped_early = True
                break

        print("-" * 50)
        print(f"✅ Evolution complete!")
        print(f"   Successes: {success_count}")
        print(f"   Rejections: {reject_count}")
        print(f"   Success Rate: {success_count/(success_count+reject_count)*100:.1f}%")
        print(f"   Best Fitness: {self.best_ever_fitness:.3f}")
        print(f"   Improvement: {((self.best_ever_fitness - self.baseline_fitness) / self.baseline_fitness * 100):.1f}%")
        if stopped_early:
            print(f"   ⏹️ Stopped early at generation {gen} (plateau)")

        return {
            'success_count': success_count,
            'reject_count': reject_count,
            'best_fitness': self.best_ever_fitness,
            'baseline_fitness': self.baseline_fitness,
            'improvement': (self.best_ever_fitness - self.baseline_fitness) / self.baseline_fitness,
            'lineage_length': self._get_lineage_length(),
            'stopped_early': stopped_early,
            'final_generation': gen if stopped_early else self.num_generations,
            'gene_effects': self.mutation_engine.get_gene_effects()
        }

    def _get_lineage_length(self) -> int:
        rows = self.db.execute(
            "SELECT COUNT(*) FROM lineage WHERE selection_reason = 'promoted' AND parent_allele_id IN (SELECT id FROM alleles WHERE gene_id = ?)",
            (self.gene_id,)
        )
        return rows[0][0] if rows else 0


# ============================================================
# CHAMPION VALIDATOR
# ============================================================

class ChampionValidator:
    def __init__(self, db: Database):
        self.db = db
        self.fitness = FitnessFunction()
        self.benchmark_runner = BenchmarkRunner(db, self.fitness)

    def validate(self, genome: Dict, num_evals: int = 50) -> Dict:
        """Validate a champion genome across multiple random seeds."""
        scores = []
        env_scores = defaultdict(list)
        
        for i in range(num_evals):
            seed = i * 1337  # Different seed for each evaluation
            
            # Create a temporary allele ID for evaluation
            temp_id = f"validation_{i}"
            
            # Evaluate across environments
            result = self.benchmark_runner.run_multi_env_benchmark(temp_id, genome)
            scores.append(result['fitness'])
            
            for env_name, env_result in result['env_scores'].items():
                env_scores[env_name].append(env_result['fitness'])
        
        # Calculate stability metrics
        mean_fitness = sum(scores) / len(scores)
        std_fitness = (sum((x - mean_fitness) ** 2 for x in scores) / len(scores)) ** 0.5
        
        return {
            'mean': mean_fitness,
            'std': std_fitness,
            'min': min(scores),
            'max': max(scores),
            'stability': 1 - (std_fitness / max(mean_fitness, 0.01)),
            'env_scores': {
                env: {
                    'mean': sum(s) / len(s),
                    'std': (sum((x - sum(s)/len(s)) ** 2 for x in s) / len(s)) ** 0.5
                }
                for env, s in env_scores.items()
            },
            'num_evaluations': num_evals
        }


# ============================================================
# EXPERIMENT RUNNER
# ============================================================

class ExperimentRunner:
    def __init__(self, db: Database):
        self.db = db
        self.genome_manager = GenomeManager(db)
        self.validator = ChampionValidator(db)

    def run(self, gene_id: str, num_generations: int = 100, plateau_generations: int = 10) -> Dict:
        seeds = [42, 1337, 9001, 12345, 8675309]
        results = []

        baseline_rows = self.db.execute(
            "SELECT baseline_fitness FROM genes WHERE id = ?",
            (gene_id,)
        )
        baseline_fitness = baseline_rows[0][0] if baseline_rows and baseline_rows[0][0] is not None else 0.5

        print(f"\n🧪 Starting MEOS V0.2 experiment for gene: {gene_id}")
        print(f"   Baseline Fitness: {baseline_fitness:.3f}")
        print(f"   Environments: {list(ENVIRONMENTS.keys())}")
        print(f"   Seeds: {seeds}")
        print("=" * 70)

        for seed in seeds:
            print(f"\n📊 Running seed {seed}...")

            seed_gene_id = self.genome_manager.create_gene(
                f"search_seed_{seed}_v2",
                f"Seed {seed} isolated evolution - V0.2"
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
                'stability': None,
                'generalization_score': None,
                'success': None,
                'started_at': datetime.now().isoformat(),
                'completed_at': None,
                'notes': ''
            })

            loop = EvolutionLoop(seed_gene_id, self.db, exp_id, num_generations, seed, 
                                baseline_fitness, plateau_generations)
            result = loop.run()

            final_fitness = result['best_fitness']
            improvement = result['improvement']

            # Validate the champion
            champion_allele = self.genome_manager.get_active_allele(seed_gene_id)
            validation = self.validator.validate(champion_allele['genome'], num_evals=20)
            stability = validation['stability']

            # Calculate generalization score (average across environments)
            gen_score = sum(v['mean'] for v in validation['env_scores'].values()) / len(validation['env_scores'])

            success = (
                final_fitness > 0.95 and
                stability > 0.90 and
                gen_score > 0.90
            )

            self.db.execute(
                "UPDATE experiments SET completed_at = ?, final_fitness = ?, improvement = ?, "
                "stability = ?, generalization_score = ?, success = ?, notes = ? WHERE id = ?",
                (datetime.now().isoformat(), final_fitness, improvement,
                 stability, gen_score, 1 if success else 0,
                 f"Successes: {result['success_count']}, Rejections: {result['reject_count']}, "
                 f"Stopped early: {result.get('stopped_early', False)}", exp_id)
            )

            # Store gene effects
            gene_effects = result.get('gene_effects', {})
            for param, data in gene_effects.items():
                self.db.insert('gene_effects', {
                    'id': str(uuid.uuid4())[:8],
                    'parameter_name': param,
                    'mutation_count': data['count'],
                    'positive_count': data.get('positive_count', 0),
                    'negative_count': data.get('negative_count', 0),
                    'avg_delta': data.get('avg_delta', 0),
                    'best_delta': data.get('best_delta', 0),
                    'worst_delta': data.get('worst_delta', 0),
                    'last_updated': datetime.now().isoformat()
                })

            results.append({
                'seed': seed,
                'success': success,
                'final_fitness': final_fitness,
                'baseline_fitness': baseline_fitness,
                'improvement': improvement,
                'stability': stability,
                'gen_score': gen_score,
                'success_count': result['success_count'],
                'reject_count': result['reject_count'],
                'lineage_length': result['lineage_length'],
                'stopped_early': result.get('stopped_early', False),
                'final_generation': result.get('final_generation', num_generations),
                'gene_effects': gene_effects
            })

            print(f"\n   Seed {seed}: {'✅ SUCCESS' if success else '❌ FAILED'}")
            print(f"   Baseline: {baseline_fitness:.3f} → Final: {final_fitness:.3f}")
            print(f"   Improvement: {improvement:.2%}")
            print(f"   Stability: {stability:.3f}")
            print(f"   Gen Score: {gen_score:.3f}")
            print(f"   Stopped Early: {'Yes' if result.get('stopped_early', False) else 'No'}")
            print(f"   Final Gen: {result.get('final_generation', num_generations)}")

        all_succeeded = all(r['success'] for r in results)
        successful_seeds = sum(1 for r in results if r['success'])

        print("\n" + "=" * 70)
        print("📊 MEOS V0.2 EXPERIMENT RESULTS")
        print(f"   All Seeds Succeeded: {'✅' if all_succeeded else '❌'}")
        print(f"   Successful Seeds: {successful_seeds}/{len(seeds)}")

        if all_succeeded:
            print("\n🎉 MEOS V0.2 SUCCEEDED!")
            print("   Genomes generalize across environments!")
        else:
            print("\n⚠️ MEOS V0.2 PARTIALLY FAILED")
            print("   Check generalization scores.")

        return {
            'all_succeeded': all_succeeded,
            'successful_seeds': successful_seeds,
            'total_seeds': len(seeds),
            'results': results,
            'baseline_fitness': baseline_fitness
        }


# ============================================================
# GENE EFFECTS ANALYZER
# ============================================================

class GeneEffectsAnalyzer:
    def __init__(self, db: Database):
        self.db = db

    def analyze(self) -> Dict:
        """Analyze gene effects from all experiments."""
        rows = self.db.execute('''
            SELECT 
                parameter_name,
                SUM(mutation_count) as total_mutations,
                SUM(positive_count) as total_positive,
                SUM(negative_count) as total_negative,
                AVG(avg_delta) as overall_avg_delta,
                MAX(best_delta) as overall_best_delta,
                MIN(worst_delta) as overall_worst_delta
            FROM gene_effects
            GROUP BY parameter_name
            ORDER BY overall_avg_delta DESC
        ''')
        
        results = {}
        for row in rows:
            results[row[0]] = {
                'total_mutations': row[1],
                'total_positive': row[2],
                'total_negative': row[3],
                'positive_rate': row[2] / row[1] if row[1] > 0 else 0,
                'avg_delta': row[4],
                'best_delta': row[5],
                'worst_delta': row[6]
            }
        
        return results

    def print_report(self):
        """Print a gene effects report."""
        effects = self.analyze()
        
        print("\n🧬 GENE EFFECTS ANALYSIS")
        print("=" * 70)
        print(f"{'Parameter':>20} | {'Mutations':>10} | {'Positive Rate':>14} | {'Avg Delta':>10}")
        print("-" * 70)
        
        for param, data in sorted(effects.items(), key=lambda x: x[1]['avg_delta'], reverse=True):
            print(f"{param:>20} | {data['total_mutations']:>10} | {data['positive_rate']:>14.2%} | {data['avg_delta']:>10.4f}")
        
        print("=" * 70)
        
        # Find most important parameters
        important = [p for p, d in effects.items() if d['positive_rate'] > 0.50 and d['avg_delta'] > 0]
        print(f"\n📈 Most important parameters (positive rate > 50%):")
        for p in important:
            print(f"  ✅ {p}: {effects[p]['positive_rate']:.1%} positive rate")
        
        neutral = [p for p, d in effects.items() if 0.30 <= d['positive_rate'] <= 0.60]
        print(f"\n⚖️ Neutral parameters (30-60% positive rate):")
        for p in neutral:
            print(f"  ⚖️ {p}: {effects[p]['positive_rate']:.1%} positive rate")
        
        negative = [p for p, d in effects.items() if d['positive_rate'] < 0.30]
        print(f"\n❌ Potentially detrimental parameters (< 30% positive rate):")
        for p in negative:
            print(f"  ❌ {p}: {effects[p]['positive_rate']:.1%} positive rate")


# ============================================================
# MAIN
# ============================================================

def main():
    print("🧬 MEOS V0.2 - Multi-Environment Evolutionary System")
    print("====================================================")
    print(f"   Environments: {list(ENVIRONMENTS.keys())}")
    print("")

    db = Database()
    genome_manager = GenomeManager(db)

    gene_id = genome_manager.create_gene("search_v2", "Multi-environment search evolution")
    print(f"📌 Created master gene: {gene_id}")

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
    results = benchmark_runner.run_multi_env_benchmark(allele_id, initial_genome)
    baseline_fitness = results['fitness']

    db.execute("UPDATE alleles SET fitness_score = ? WHERE id = ?", (baseline_fitness, allele_id))
    genome_manager.set_active_allele(allele_id)
    genome_manager.set_baseline_fitness(gene_id, baseline_fitness)

    print(f"   Baseline fitness: {baseline_fitness:.3f}")
    print(f"   Baseline genome: {initial_genome}")

    # Run experiment with plateau detection
    runner = ExperimentRunner(db)
    result = runner.run(gene_id, num_generations=100, plateau_generations=10)

    # Analyze gene effects
    analyzer = GeneEffectsAnalyzer(db)
    analyzer.print_report()

    print("\n" + "=" * 70)
    if result['all_succeeded']:
        print("🎉 MEOS V0.2 COMPLETED SUCCESSFULLY!")
        print("   Genomes generalize across environments!")
        print("\n✅ Proceed to MEOS V0.3")
    else:
        print("⚠️ MEOS V0.2 COMPLETED WITH ISSUES")
        print(f"   {result['successful_seeds']}/{result['total_seeds']} seeds succeeded.")
        print("\n   Check generalization scores and stability.")

    print("\n📁 Data stored in: data/meos_v0.2.db")
    print("📊 Run: python analyze_v0.2.py")

    # Save champion genomes
    print("\n🏆 Champion Genomes:")
    for r in result['results']:
        if r['success']:
            print(f"   Seed {r['seed']}: Fitness {r['final_fitness']:.4f} (Improvement: {r['improvement']:.2%})")


if __name__ == "__main__":
    main()