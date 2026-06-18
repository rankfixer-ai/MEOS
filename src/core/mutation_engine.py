import json
import random
import uuid
import hashlib
from typing import Dict, List, Tuple, Any
from collections import defaultdict


class MutationEngine:
    def __init__(self, random_seed: int = 42):
        self.random = random.Random(random_seed)
        self.mutation_attempts = 0
        self.MIN_IMPROVEMENT = 0.005
        self._gene_effects = defaultdict(lambda: {
            'positive': 0, 'negative': 0, 'neutral': 0,
            'total_delta': 0, 'count': 0
        })
        self._mutation_events = []

    def mutate(self, genome: Dict, generation: int) -> Tuple[Dict, Dict]:
        """
        Mutate a genome. Always mutates at least one parameter.
        Returns: (new_genome, diff)
        """
        self.mutation_attempts += 1
        new_genome = json.loads(json.dumps(genome))

        params = ['parallelism', 'cache_enabled', 'cache_size', 'reranking_enabled',
                  'batch_size', 'timeout_seconds', 'max_results']
        num_mutations = self.random.choice([1, 1, 1, 2, 2, 3])

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
                diff[param] = {'old': old_value, 'new': new_value}
                
                event = {
                    'parameter': param,
                    'mutation_type': self._get_mutation_type(param, old_value, new_value),
                    'mutation_order': event_order,
                    'old_value': str(old_value),
                    'new_value': str(new_value)
                }
                self._mutation_events.append(event)
                event_order += 1

        if not diff:
            param = self.random.choice(params)
            old_value = genome[param]
            new_value = self._mutate_param(param, old_value)
            new_genome[param] = new_value
            diff[param] = {'old': old_value, 'new': new_value}
            
            event = {
                'parameter': param,
                'mutation_type': self._get_mutation_type(param, old_value, new_value),
                'mutation_order': 0,
                'old_value': str(old_value),
                'new_value': str(new_value)
            }
            self._mutation_events.append(event)

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

    @staticmethod
    def hash_genome(genome: Dict) -> str:
        """Deterministic genome hash for reproducibility."""
        return hashlib.md5(
            json.dumps(
                genome,
                sort_keys=True,
                separators=(",", ":")
            ).encode()
        ).hexdigest()[:16]

    def record_mutation_trial(
        self,
        db,
        parent_allele_id: str,
        child_allele_id: str,
        run_id: str,
        seed: int,
        generation: int,
        fitness_before: float,
        fitness_after: float,
        accepted_parent_fitness: float,
        parent_genome_hash: str,
        child_genome_hash: str,
        evaluation_result: str
    ):
        """Record a mutation trial and its events."""
        delta = fitness_after - fitness_before
        mutation_count = len(self._mutation_events)
        
        # Equal attribution model.
        # Multi-gene mutations split fitness gain equally.
        # Future versions may replace this with interaction-aware attribution.
        attributed_delta = delta / mutation_count if mutation_count > 0 else 0
        
        trial_id = uuid.uuid4().hex[:16]
        
        # Insert trial
        db.insert('mutation_trials', {
            'id': trial_id,
            'parent_allele_id': parent_allele_id,
            'child_allele_id': child_allele_id,
            'run_id': run_id,
            'seed': seed,
            'generation': generation,
            'fitness_before': fitness_before,
            'fitness_after': fitness_after,
            'accepted_parent_fitness': accepted_parent_fitness,
            'delta': delta,
            'parent_genome_hash': parent_genome_hash,
            'child_genome_hash': child_genome_hash,
            'evaluation_result': evaluation_result
        })
        
        # Insert events
        for event in self._mutation_events:
            db.insert('mutation_events', {
                'id': uuid.uuid4().hex[:16],
                'trial_id': trial_id,
                'parameter': event['parameter'],
                'mutation_type': event['mutation_type'],
                'mutation_order': event['mutation_order'],
                'old_value': event['old_value'],
                'new_value': event['new_value']
            })
        
        # Update attribution with SPLIT delta
        for event in self._mutation_events:
            self._record_effect(event['parameter'], attributed_delta)

    def _record_effect(self, param: str, delta: float):
        if param not in self._gene_effects:
            self._gene_effects[param] = {'positive': 0, 'negative': 0, 'neutral': 0, 'total_delta': 0, 'count': 0}
        
        self._gene_effects[param]['count'] += 1
        self._gene_effects[param]['total_delta'] += delta
        
        if delta > 0:
            self._gene_effects[param]['positive'] += 1
        elif delta < 0:
            self._gene_effects[param]['negative'] += 1
        else:
            self._gene_effects[param]['neutral'] += 1

    def get_gene_effects(self) -> Dict:
        result = {}
        for param, data in self._gene_effects.items():
            if data['count'] > 0:
                result[param] = {
                    'count': data['count'],
                    'positive': data['positive'],
                    'negative': data['negative'],
                    'neutral': data['neutral'],
                    'positive_rate': data['positive'] / data['count'],
                    'negative_rate': data['negative'] / data['count'],
                    'neutral_rate': data['neutral'] / data['count'],
                    'avg_delta': data['total_delta'] / data['count'],
                    'total_delta': data['total_delta']
                }
        return result